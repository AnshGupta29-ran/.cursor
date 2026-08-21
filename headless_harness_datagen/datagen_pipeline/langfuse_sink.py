"""Langfuse Python SDK v4 sink (Chakra-compatible env keys).

Chakra gRPC does not push model turns to Langfuse. Autopilot must:
  - create a session + per-task trace
  - mirror live harness events (turns/tools) into Langfuse generations/spans
  - attach repo + JSONL samples when a task finishes

Env (same as Chakra):
  LANGFUSE_PUBLIC_KEY
  LANGFUSE_SECRET_KEY
  LANGFUSE_HOST
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_dotenv_langfuse() -> None:
    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        return
    try:
        from datagen_pipeline.paths import ROOT

        env_path = ROOT / ".env"
        if not env_path.is_file():
            return
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k = k.strip()
            if k.startswith("LANGFUSE_") and (k not in os.environ or not os.environ.get(k)):
                os.environ[k] = v.strip().strip('"').strip("'")
    except Exception:
        pass


def _clip(text: Any, n: int = 4000) -> str:
    s = str(text or "")
    if len(s) <= n:
        return s
    return s[: n - 20] + "\n...[truncated]..."


class _Obs:
    def __init__(self, obs: Any, client: Any, exits: list | None = None) -> None:
        self._obs = obs
        self._client = client
        self._exits = exits or []

    def update(self, **kwargs: Any) -> None:
        try:
            self._obs.update(**kwargs)
        except Exception:
            pass

    def span(self, name: str, **kwargs: Any) -> Any:
        try:
            child = self._obs.start_observation(as_type="span", name=name, **kwargs)
            return _Obs(child, self._client)
        except Exception:
            return None

    def generation(self, name: str, **kwargs: Any) -> Any:
        try:
            child = self._obs.start_observation(as_type="generation", name=name, **kwargs)
            return _Obs(child, self._client)
        except Exception:
            try:
                child = self._obs.start_observation(as_type="span", name=name, **kwargs)
                return _Obs(child, self._client)
            except Exception:
                return None

    def end(self) -> None:
        # Prefer context __exit__ (ends the observation once). Calling both
        # .end() and __exit__ triggers "Calling end() on an ended span".
        if self._exits:
            for ctx in reversed(self._exits):
                try:
                    ctx.__exit__(None, None, None)
                except Exception:
                    pass
            self._exits.clear()
            return
        try:
            self._obs.end()
        except Exception:
            pass


class LangfuseSink:
    def __init__(self) -> None:
        _load_dotenv_langfuse()
        self.enabled = bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
        self._client = None
        self.session_id: str | None = None
        self.run_name: str | None = None
        self._live_stop: threading.Event | None = None
        self._live_thread: threading.Thread | None = None
        # Live mirror floods stderr when fuse.tensorstudio.ai times out.
        # Default OFF; set DATAGEN_LANGFUSE_LIVE=1 to stream turns/tools.
        live_raw = (os.getenv("DATAGEN_LANGFUSE_LIVE") or "0").strip().lower()
        self.live_mirror_enabled = live_raw in {"1", "true", "yes", "on"}
        if self.enabled:
            try:
                # Quiet OpenTelemetry exporter noise (502 / read timeout spam).
                os.environ.setdefault("OTEL_LOG_LEVEL", "ERROR")
                try:
                    import logging

                    for name in (
                        "opentelemetry",
                        "opentelemetry.exporter",
                        "opentelemetry.sdk",
                        "urllib3",
                    ):
                        logging.getLogger(name).setLevel(logging.CRITICAL)
                except Exception:
                    pass
                from langfuse import Langfuse  # type: ignore

                host = os.getenv("LANGFUSE_HOST") or "https://cloud.langfuse.com"
                kwargs = {
                    "public_key": os.environ["LANGFUSE_PUBLIC_KEY"],
                    "secret_key": os.environ["LANGFUSE_SECRET_KEY"],
                    "host": host,
                }
                try:
                    self._client = Langfuse(
                        **kwargs,
                        timeout=int(os.getenv("LANGFUSE_TIMEOUT") or "30"),
                    )
                except TypeError:
                    self._client = Langfuse(**kwargs)
                try:
                    ok = self._client.auth_check()
                    print(f"[langfuse] auth_check={ok} (SDK v4)", flush=True)
                except Exception as exc:  # noqa: BLE001
                    print(f"[langfuse] auth_check warn: {exc}", flush=True)
            except Exception as exc:  # noqa: BLE001
                print(f"[langfuse] disabled: {exc}", flush=True)
                self.enabled = False
                self._client = None

    def _open_observation(
        self,
        *,
        name: str,
        metadata: dict[str, Any],
        tags: list[str] | None = None,
        as_type: str = "span",
    ) -> _Obs | None:
        assert self._client is not None
        from langfuse import propagate_attributes  # type: ignore

        exits: list[Any] = []
        try:
            p = propagate_attributes(
                session_id=self.session_id,
                tags=[t for t in (tags or []) if t],
                metadata={k: str(v) for k, v in metadata.items() if v is not None},
                trace_name=name,
            )
            p.__enter__()
            exits.append(p)
        except Exception as exc:  # noqa: BLE001
            print(f"[langfuse] propagate_attributes warn: {exc}", flush=True)

        try:
            cm = self._client.start_as_current_observation(
                as_type=as_type,
                name=name,
                metadata=metadata,
            )
            span = cm.__enter__()
            exits.append(cm)
            return _Obs(span, self._client, exits=exits)
        except Exception:
            try:
                span = self._client.start_observation(
                    as_type=as_type, name=name, metadata=metadata
                )
                return _Obs(span, self._client, exits=exits)
            except Exception as exc:  # noqa: BLE001
                for ctx in reversed(exits):
                    try:
                        ctx.__exit__(None, None, None)
                    except Exception:
                        pass
                raise exc

    def start_run_session(
        self,
        *,
        model: str = "kimi3",
        mode: str = "autopilot",
        meta: dict[str, Any] | None = None,
    ) -> str | None:
        if not self.enabled or self._client is None:
            print(
                "[langfuse] OFF — set LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY",
                flush=True,
            )
            return None
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.session_id = f"datagen-{mode}-{stamp}-{uuid.uuid4().hex[:8]}"
        self.run_name = f"datagen_autopilot:{stamp}"
        try:
            root = self._open_observation(
                name=self.run_name,
                metadata={
                    "mode": mode,
                    "model": model,
                    "started_at": stamp,
                    "session_id": self.session_id,
                    **(meta or {}),
                },
                tags=["datagen_pipeline", mode, model, "autopilot_session"],
            )
            if root:
                root.update(
                    input={
                        "pipeline": "datagen_autopilot",
                        "model": model,
                        "meta": meta or {},
                    },
                    output={"status": "session_started", "session_id": self.session_id},
                )
                root.end()
            self.flush()
            host = (os.getenv("LANGFUSE_HOST") or "https://cloud.langfuse.com").rstrip("/")
            print(f"[langfuse] ON session_id={self.session_id}", flush=True)
            print(f"[langfuse] UI: {host}", flush=True)
            if self.live_mirror_enabled:
                print(
                    "[langfuse] live mirror ON — task turns/tools stream into this session",
                    flush=True,
                )
            else:
                print(
                    "[langfuse] live mirror OFF (set DATAGEN_LANGFUSE_LIVE=1 to enable; "
                    "reduces fuse timeout spam)",
                    flush=True,
                )
            return self.session_id
        except Exception as exc:  # noqa: BLE001
            print(f"[langfuse] session start failed: {exc}", flush=True)
            return None

    def start_task_trace(self, *, task_key: str, metadata: dict[str, Any]) -> Any:
        if not self.enabled or self._client is None:
            return None
        try:
            md = {**metadata, "task_key": task_key, "session_id": self.session_id}
            tags = [
                "datagen_pipeline",
                str(metadata.get("category") or ""),
                str(metadata.get("mode") or "autopilot"),
                str(metadata.get("language") or ""),
            ]
            return self._open_observation(
                name=f"datagen:{task_key}",
                metadata=md,
                tags=tags,
                as_type="span",
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[langfuse] trace failed: {exc}", flush=True)
            return None

    def span(self, trace: Any, name: str, **kwargs: Any) -> Any:
        if isinstance(trace, _Obs):
            return trace.span(name, **kwargs)
        return None

    def end_ok(self, trace: Any, *, output: dict[str, Any] | None = None) -> None:
        self.stop_live_mirror()
        if isinstance(trace, _Obs):
            trace.update(output=output or {"status": "done"})
            trace.end()
        self.flush()

    def end_error(self, trace: Any, error: str) -> None:
        self.stop_live_mirror()
        if isinstance(trace, _Obs):
            try:
                trace.update(output={"status": "failed", "error": error[:2000]}, level="ERROR")
            except Exception:
                trace.update(output={"status": "failed", "error": error[:2000]})
            trace.end()
        self.flush()

    def end_run_session(self, *, ok: int, failed: int) -> None:
        self.stop_live_mirror()
        if not self.enabled or not self.session_id or self._client is None:
            return
        try:
            root = self._open_observation(
                name=f"{self.run_name or 'datagen_autopilot'}:summary",
                metadata={"ok": ok, "failed": failed, "session_id": self.session_id},
                tags=["datagen_pipeline", "autopilot_summary"],
            )
            if root:
                root.update(output={"ok": ok, "failed": failed, "status": "session_finished"})
                root.end()
        except Exception:
            pass
        self.flush()

    def start_live_mirror(
        self,
        *,
        task_trace: Any,
        logs_root: Path,
        task_key: str,
        model: str,
        poll_seconds: float = 2.0,
    ) -> None:
        """Tail newest harness trace.jsonl and mirror turns/tools into Langfuse live."""
        self.stop_live_mirror()
        if not self.live_mirror_enabled:
            return
        if not self.enabled or not isinstance(task_trace, _Obs):
            return
        stop = threading.Event()
        self._live_stop = stop

        def _worker() -> None:
            offset = 0
            current: Path | None = None
            open_gens: dict[str, _Obs] = {}
            text_bufs: dict[str, list[str]] = {}
            events_pushed = 0
            last_flush = time.time()
            while not stop.is_set():
                try:
                    newest = self._newest_trace_jsonl(logs_root)
                    if newest is None:
                        stop.wait(poll_seconds)
                        continue
                    if current is None or newest != current:
                        current = newest
                        offset = 0
                        task_trace.update(
                            metadata={
                                "live_trace_path": str(current),
                                "task_key": task_key,
                            }
                        )
                    with current.open("r", encoding="utf-8", errors="replace") as fh:
                        fh.seek(offset)
                        while True:
                            line = fh.readline()
                            if not line:
                                break
                            offset = fh.tell()
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                ev = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            n = self._mirror_event(
                                task_trace,
                                ev,
                                open_gens=open_gens,
                                text_bufs=text_bufs,
                                model=model,
                                task_key=task_key,
                            )
                            events_pushed += n
                    if events_pushed and time.time() - last_flush >= 5.0:
                        self.flush()
                        last_flush = time.time()
                        task_trace.update(
                            output={
                                "status": "running",
                                "mirrored_events": events_pushed,
                                "trace_path": str(current) if current else None,
                            }
                        )
                except Exception as exc:  # noqa: BLE001
                    print(f"[langfuse] live mirror warn: {exc}", flush=True)
                stop.wait(poll_seconds)
            # close dangling generations
            for gen in list(open_gens.values()):
                try:
                    gen.update(output={"status": "interrupted"})
                    gen.end()
                except Exception:
                    pass
            open_gens.clear()
            self.flush()

        t = threading.Thread(
            target=_worker,
            name=f"langfuse-live-{task_key[:40]}",
            daemon=True,
        )
        self._live_thread = t
        t.start()

    def stop_live_mirror(self) -> None:
        stop = self._live_stop
        thread = self._live_thread
        self._live_stop = None
        self._live_thread = None
        if stop is not None:
            stop.set()
        if thread is not None and thread.is_alive():
            thread.join(timeout=5.0)

    @staticmethod
    def _newest_trace_jsonl(logs_root: Path) -> Path | None:
        if not logs_root.is_dir():
            return None
        candidates = list(logs_root.glob("*/pipeline/working/trace.jsonl"))
        if not candidates:
            candidates = list(logs_root.glob("**/pipeline/working/trace.jsonl"))
        if not candidates:
            return None
        return max(candidates, key=lambda p: p.stat().st_mtime)

    def _mirror_event(
        self,
        task_trace: _Obs,
        ev: dict[str, Any],
        *,
        open_gens: dict[str, _Obs],
        text_bufs: dict[str, list[str]],
        model: str,
        task_key: str,
    ) -> int:
        et = str(ev.get("type") or "")
        turn_id = str(ev.get("turn_id") or ev.get("conversation_id") or "")
        if et == "backend_turn_start":
            prev = open_gens.pop(turn_id, None)
            if prev is not None:
                try:
                    prev.end()
                except Exception:
                    pass
            text_bufs[turn_id] = []
            gen = task_trace.generation(
                name=f"turn:{turn_id[:8] or 'start'}",
                model=model,
                input={"message": _clip(ev.get("message"), 6000)},
                metadata={
                    "event": et,
                    "task_key": task_key,
                    "turn_id": turn_id,
                    "ts": ev.get("ts"),
                },
            )
            if gen is not None and turn_id:
                open_gens[turn_id] = gen
            return 1 if gen is not None else 0

        if et == "assistant_text_delta":
            chunk = str(ev.get("text") or ev.get("delta") or "")
            if not chunk:
                return 0
            buf = text_bufs.setdefault(turn_id, [])
            buf.append(chunk)
            gen = open_gens.get(turn_id)
            # Throttle generation updates: every ~40 chunks or ~800 chars.
            joined_len = sum(len(x) for x in buf)
            if gen is not None and (len(buf) % 40 == 0 or joined_len % 800 < len(chunk)):
                gen.update(output={"thinking_partial": _clip("".join(buf), 8000)})
            return 1

        if et in {"assistant_message", "stream_turn_finished", "token_usage"}:
            gen = open_gens.get(turn_id)
            usage = ev.get("usage") if isinstance(ev.get("usage"), dict) else {}
            text = ev.get("text") or ev.get("message") or ev.get("summary") or ""
            if not str(text).strip():
                text = "".join(text_bufs.get(turn_id) or [])
            orch = ev.get("orchestration") if isinstance(ev.get("orchestration"), dict) else {}
            if gen is None and et != "token_usage":
                gen = task_trace.generation(
                    name=f"turn_out:{turn_id[:8] or et}",
                    model=model,
                    metadata={"event": et, "task_key": task_key, "turn_id": turn_id},
                )
                if gen is not None and turn_id:
                    open_gens[turn_id] = gen
            if gen is None:
                return 0
            payload: dict[str, Any] = {
                "event": et,
                "text": _clip(text, 8000),
            }
            if orch:
                payload["turn_count"] = orch.get("turn_count")
                payload["completion_detected"] = orch.get("completion_detected")
            update_kwargs: dict[str, Any] = {"output": payload}
            pt = usage.get("prompt_tokens") or ev.get("prompt_tokens")
            ct = usage.get("completion_tokens") or ev.get("completion_tokens")
            if pt is not None or ct is not None:
                update_kwargs["usage_details"] = {
                    "input": int(pt or 0),
                    "output": int(ct or 0),
                }
            gen.update(**update_kwargs)
            if et in {"assistant_message", "stream_turn_finished"}:
                open_gens.pop(turn_id, None)
                text_bufs.pop(turn_id, None)
                gen.end()
            return 1

        if et == "tool_request":
            child = task_trace.span(
                name=f"tool:{ev.get('tool_name') or 'unknown'}",
                input={
                    "tool_name": ev.get("tool_name"),
                    "arguments": ev.get("arguments"),
                },
                metadata={
                    "turn_id": turn_id,
                    "invocation_id": ev.get("invocation_id"),
                    "event": et,
                },
            )
            if child is not None:
                inv = str(ev.get("invocation_id") or "")
                if inv:
                    open_gens[f"tool:{inv}"] = child
                else:
                    child.end()
            return 1 if child is not None else 0

        if et == "tool_response":
            inv = str(ev.get("invocation_id") or "")
            child = open_gens.pop(f"tool:{inv}", None) if inv else None
            if child is None:
                child = task_trace.span(
                    name=f"tool_result:{ev.get('tool_name') or 'unknown'}",
                    metadata={"event": et, "turn_id": turn_id},
                )
            if child is None:
                return 0
            child.update(
                output={
                    "tool_name": ev.get("tool_name"),
                    "is_error": ev.get("is_error"),
                    "output": _clip(ev.get("output"), 3000),
                }
            )
            child.end()
            return 1

        if et in {"tool_approval", "controller_decision", "run_started"}:
            child = task_trace.span(
                name=et,
                input={
                    k: ev.get(k)
                    for k in ("decision", "kind", "reason", "response", "reasoning")
                    if k in ev
                },
                metadata={"event": et, "ts": ev.get("ts")},
            )
            if child is not None:
                child.end()
                return 1
        return 0

    def attach_run_artifacts(
        self,
        trace: Any,
        *,
        task_key: str,
        workdir: str,
        logs_root: Path | None = None,
        max_events: int = 800,
    ) -> None:
        if not isinstance(trace, _Obs):
            return
        try:
            from datagen_pipeline.paths import CHAKRA_DIR, ROOT

            repo = CHAKRA_DIR / workdir
            if not repo.is_dir():
                repo = ROOT / "experiments" / workdir
            meta: dict[str, Any] = {
                "task_key": task_key,
                "repo_path": str(repo) if repo.exists() else workdir,
                "repo_exists": repo.exists(),
                "session_id": self.session_id,
            }
            if repo.exists():
                files = [
                    str(p.relative_to(repo))
                    for p in repo.rglob("*")
                    if p.is_file()
                    and "node_modules" not in p.parts
                    and ".git" not in p.parts
                ][:80]
                meta["repo_file_sample"] = files
                meta["repo_file_count_sample"] = len(files)
            child = self.span(trace, "repo", metadata=meta)
            if child:
                child.end()

            root = logs_root or (ROOT / "logs")
            if root.is_dir():
                candidates = list(root.glob("*/pipeline/working/trace.jsonl"))
                if not candidates:
                    candidates = list(root.glob("**/pipeline/working/trace.jsonl"))
                if not candidates:
                    candidates = list(root.glob("**/raw_events.jsonl"))
                if candidates:
                    newest = max(candidates, key=lambda p: p.stat().st_mtime)
                    self.attach_jsonl_trace(trace, newest, max_events=max_events)
        except Exception as exc:  # noqa: BLE001
            print(f"[langfuse] attach_run_artifacts skipped: {exc}", flush=True)

    def attach_jsonl_trace(self, trace: Any, path: Path, max_events: int = 500) -> None:
        if not isinstance(trace, _Obs) or not path.is_file():
            return
        events: list[dict] = []
        try:
            with path.open(encoding="utf-8") as fh:
                for i, line in enumerate(fh):
                    if i >= max_events:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            child = self.span(
                trace,
                "harness_jsonl_sample",
                input={
                    "path": str(path),
                    "event_count": len(events),
                    "events_preview": events[:40],
                },
                metadata={"truncated": len(events) >= max_events},
            )
            if child:
                child.end()
        except Exception as exc:  # noqa: BLE001
            print(f"[langfuse] attach jsonl skipped: {exc}", flush=True)

    def flush(self) -> None:
        if self._client is None:
            return
        try:
            self._client.flush()
        except Exception as exc:  # noqa: BLE001
            # fuse.tensorstudio.ai read timeouts must not look like crashes.
            print(f"[langfuse] flush warn: {exc}", flush=True)
