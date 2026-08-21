"""Pull exact billed token usage from Langfuse into the prompt_stats ledger.

Chakra/kimi OpenAI-compat proxies often omit `usage` in session JSONL, so the
dashboard cannot see charged tokens from transcripts alone. Langfuse (when the
autopilot sink is enabled) stores generation usage — use that as the bill source.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from prompt_stats.ledger import prompt_fingerprint, record_id_for, upsert_merge, utc_now


def _parse_dt(s: Any) -> datetime | None:
    if s is None:
        return None
    if isinstance(s, datetime):
        return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def collect_langfuse_usage(*, since: str | None = None, limit: int = 200) -> int:
    """Fetch recent Langfuse observations and upsert exact token rows.

    Returns number of ledger rows written/updated.
    """
    pk = os.getenv("LANGFUSE_PUBLIC_KEY")
    sk = os.getenv("LANGFUSE_SECRET_KEY")
    if not pk or not sk:
        return 0
    try:
        from langfuse import Langfuse  # type: ignore
    except ImportError:
        return 0

    host = os.getenv("LANGFUSE_HOST") or "https://cloud.langfuse.com"
    try:
        client = Langfuse(public_key=pk, secret_key=sk, host=host)
    except Exception:
        return 0

    since_dt = None
    if since:
        since_dt = _parse_dt(since if "T" in since else since + "T00:00:00+00:00")

    written = 0
    traces: list[Any] = []
    try:
        api = getattr(client, "api", None)
        if api is None:
            return 0
        # SDK v4 REST: trace.list
        trace_api = getattr(api, "trace", None)
        if trace_api is None:
            return 0
        kwargs: dict[str, Any] = {"limit": min(100, limit)}
        if since_dt is not None:
            kwargs["from_timestamp"] = since_dt
        page = trace_api.list(**kwargs)
        data = getattr(page, "data", None) or getattr(page, "traces", None) or page
        if isinstance(data, list):
            traces = data
        elif hasattr(data, "__iter__"):
            traces = list(data)
    except Exception as exc:  # noqa: BLE001
        print(f"  langfuse usage pull skipped: {exc}", flush=True)
        return 0

    obs_api = getattr(api, "observations", None) or getattr(api, "observation", None)

    for tr in traces[:limit]:
        try:
            tid = getattr(tr, "id", None) or (tr.get("id") if isinstance(tr, dict) else None)
            session_id = getattr(tr, "session_id", None) or (
                tr.get("session_id") if isinstance(tr, dict) else None
            )
            name = getattr(tr, "name", None) or (tr.get("name") if isinstance(tr, dict) else None)
            ts = (
                getattr(tr, "timestamp", None)
                or getattr(tr, "created_at", None)
                or (tr.get("timestamp") if isinstance(tr, dict) else None)
                or (tr.get("created_at") if isinstance(tr, dict) else None)
            )
            meta = getattr(tr, "metadata", None) or (
                tr.get("metadata") if isinstance(tr, dict) else None
            ) or {}
            model = None
            if isinstance(meta, dict):
                model = meta.get("model") or meta.get("OPENAI_MODEL")

            tin = tout = 0
            # Prefer observation-level usage if available
            if obs_api is not None and tid:
                try:
                    obs_page = obs_api.get_many(trace_id=tid, limit=100)
                    obs_list = (
                        getattr(obs_page, "data", None)
                        or getattr(obs_page, "observations", None)
                        or obs_page
                    )
                    if not isinstance(obs_list, list):
                        obs_list = list(obs_list) if obs_list else []
                    for obs in obs_list:
                        usage = getattr(obs, "usage", None) or (
                            obs.get("usage") if isinstance(obs, dict) else None
                        )
                        if not usage:
                            # v3/v4 alternate fields
                            tin += int(
                                getattr(obs, "input_usage", 0)
                                or (obs.get("input_usage") if isinstance(obs, dict) else 0)
                                or 0
                            )
                            tout += int(
                                getattr(obs, "output_usage", 0)
                                or (obs.get("output_usage") if isinstance(obs, dict) else 0)
                                or 0
                            )
                            om = getattr(obs, "model", None) or (
                                obs.get("model") if isinstance(obs, dict) else None
                            )
                            if om and not model:
                                model = om
                            continue
                        if isinstance(usage, dict):
                            tin += int(
                                usage.get("input")
                                or usage.get("input_tokens")
                                or usage.get("prompt_tokens")
                                or 0
                            )
                            tout += int(
                                usage.get("output")
                                or usage.get("output_tokens")
                                or usage.get("completion_tokens")
                                or 0
                            )
                        else:
                            tin += int(getattr(usage, "input", 0) or getattr(usage, "input_tokens", 0) or 0)
                            tout += int(
                                getattr(usage, "output", 0) or getattr(usage, "output_tokens", 0) or 0
                            )
                        om = getattr(obs, "model", None) or (
                            obs.get("model") if isinstance(obs, dict) else None
                        )
                        if om and not model:
                            model = om
                except Exception:
                    pass

            # Trace-level totals as fallback
            if tin == 0 and tout == 0:
                for attr in ("total_cost",):
                    pass
                tin = int(
                    getattr(tr, "input_tokens", 0)
                    or (tr.get("input_tokens") if isinstance(tr, dict) else 0)
                    or 0
                )
                tout = int(
                    getattr(tr, "output_tokens", 0)
                    or (tr.get("output_tokens") if isinstance(tr, dict) else 0)
                    or 0
                )

            if tin == 0 and tout == 0:
                continue

            model_s = str(model or "kimi3")
            if "kimi" not in model_s.lower() and not str(session_id or "").startswith("datagen-"):
                # Keep non-kimi if session is our autopilot; else skip
                if not str(name or "").startswith("datagen"):
                    continue
                model_s = model_s or "kimi3"

            when = _parse_dt(ts)
            if since_dt and when and when < since_dt:
                continue

            fp = prompt_fingerprint(f"langfuse|{tid}|{tin}|{tout}")
            rid = record_id_for(source="langfuse_usage", key=str(tid or session_id), fingerprint=fp)
            upsert_merge(
                {
                    "id": rid,
                    "source": "langfuse_usage",
                    "kind": "billed_usage",
                    "agent": "chakra",
                    "title": f"Langfuse {name or tid}"[:120],
                    "seed": str(session_id or ""),
                    "prompt_fingerprint": fp,
                    "session_id": session_id,
                    "model": model_s if "kimi" in model_s.lower() else f"kimi3/{model_s}",
                    "event_time": when.isoformat() if when else utc_now(),
                    "input_tokens": tin,
                    "output_tokens": tout,
                    "total_tokens": tin + tout,
                    "input_tokens_api": tin,
                    "output_tokens_api": tout,
                    "total_tokens_api": tin + tout,
                    "tokens_are_estimated": False,
                    "tokens_source": "langfuse",
                    "langfuse_trace_id": tid,
                    "schema_version": 1,
                    "recorded_at": utc_now(),
                }
            )
            written += 1
        except Exception:
            continue

    try:
        client.flush()
    except Exception:
        pass
    if written:
        print(f"  langfuse exact usage rows: {written}", flush=True)
    return written
