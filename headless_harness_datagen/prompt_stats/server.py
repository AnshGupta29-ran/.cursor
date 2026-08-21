"""Local analytics server with live Chakra history sync."""

from __future__ import annotations

import json
import os
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from prompt_stats.collectors import (
    collect_chakra_history,
    collect_chakra_sessions,
    collect_pi_sessions,
    refresh_all,
)
from prompt_stats.datagen_views import dimensions_catalog
from prompt_stats.ledger import LEDGER_PATH, ensure_stats_dir, load_records
from prompt_stats.report import summarize, write_dashboard
from prompt_stats.usage_views import usage_report

STATIC_DIR = Path(__file__).resolve().parent / "static"

_sync_lock = threading.Lock()


def _live_sync() -> dict[str, Any]:
    """Pull Chakra + Pi session transcripts (time/tokens) then history stubs."""
    n_sess = collect_chakra_sessions()
    n_pi = collect_pi_sessions()
    n_hist = collect_chakra_history()
    n_lf = 0
    try:
        from prompt_stats.langfuse_usage import collect_langfuse_usage

        n_lf = collect_langfuse_usage(since=os.getenv("DATAGEN_KIMI3_SINCE", "2026-08-13"))
    except Exception as exc:  # noqa: BLE001
        print(f"langfuse usage sync skipped: {exc}", flush=True)
    write_dashboard()
    payload = summarize(load_records())
    payload["synced_chakra_sessions"] = n_sess
    payload["synced_pi_sessions"] = n_pi
    payload["synced_chakra_history_rows"] = n_hist
    payload["synced_langfuse_usage"] = n_lf
    return payload


def _safe_live_sync() -> dict[str, Any]:
    """Serialize sync so overlapping UI polls don't stack and hang the server."""
    if not _sync_lock.acquire(blocking=False):
        payload = summarize(load_records())
        payload["synced_chakra_sessions"] = 0
        payload["synced_pi_sessions"] = 0
        payload["synced_chakra_history_rows"] = 0
        payload["sync_skipped"] = "busy"
        return payload
    try:
        return _live_sync()
    except Exception as exc:
        payload = summarize(load_records())
        payload["sync_error"] = str(exc)
        return payload
    finally:
        _sync_lock.release()


def _safe_refresh() -> dict[str, Any]:
    acquired = _sync_lock.acquire(timeout=120)
    if not acquired:
        payload = summarize(load_records())
        payload["sync_skipped"] = "busy"
        return payload
    try:
        counts = refresh_all()
        write_dashboard()
        payload = summarize(load_records())
        payload["backfill"] = counts
        return payload
    except Exception as exc:
        payload = summarize(load_records())
        payload["sync_error"] = str(exc)
        return payload
    finally:
        _sync_lock.release()


class StatsHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, fmt: str, *args) -> None:  # quieter
        pass

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return
        if path == "/api/health":
            self._json({"ok": True})
            return
        if path == "/api/summary":
            self._json(summarize(load_records()))
            return
        if path == "/api/records":
            self._json({"records": load_records(), "count": len(load_records())})
            return
        if path == "/api/sync":
            self._json(_safe_live_sync())
            return
        if path == "/api/refresh":
            self._json(_safe_refresh())
            return
        if path == "/api/kimi3":
            qs = parse_qs(urlparse(self.path).query)
            since = (qs.get("since") or ["2026-08-13"])[0]
            full = usage_report(since=since)

            def is_kimi_row(r: dict) -> bool:
                return "kimi" in str(r.get("model") or "").lower()

            rows = [r for r in (full.get("rows") or []) if is_kimi_row(r)]
            tasks = [t for t in (full.get("by_task") or []) if is_kimi_row(t)]
            models = [m for m in (full.get("by_model") or []) if "kimi" in str(m.get("key") or "").lower()]
            # Recompute charged/est from filtered rows to avoid mixing other models
            charged_in = sum(int(r.get("charged_input") or 0) for r in rows)
            charged_out = sum(int(r.get("charged_output") or 0) for r in rows)
            # Prefer model-slice est from by_model kimi entries
            est_in = sum(int(m.get("est_input") or 0) for m in models)
            est_out = sum(int(m.get("est_output") or 0) for m in models)
            runtime = sum(float(m.get("runtime_seconds") or 0) for m in models)
            if not models:
                est_in = sum(int(r.get("est_input") or 0) for r in rows)
                est_out = sum(int(r.get("est_output") or 0) for r in rows)
                runtime = sum(float(r.get("runtime_seconds") or 0) for r in rows if r.get("source", "").endswith("_session") or r.get("source") == "autopilot_task")
            payload = {
                **full,
                "rows": rows,
                "by_task": tasks,
                "by_model": models,
                "charged_input": charged_in,
                "charged_output": charged_out,
                "charged_total": charged_in + charged_out,
                "est_input": est_in,
                "est_output": est_out,
                "est_total": est_in + est_out,
                "runtime_seconds": runtime,
                "exact_rows": sum(1 for r in rows if r.get("exact")),
                "input_tokens": charged_in,
                "output_tokens": charged_out,
                "total_tokens": charged_in + charged_out,
                "provider_note": full.get("note"),
                "tasks": rows,
            }
            self._json(payload)
            return
        if path == "/api/usage":
            qs = parse_qs(urlparse(self.path).query)
            self._json(
                usage_report(
                    since=(qs.get("since") or [None])[0],
                    agent=(qs.get("agent") or [None])[0] or None,
                    model=(qs.get("model") or [None])[0] or None,
                )
            )
            return
        if path == "/api/dimensions":
            self._json(dimensions_catalog())
            return
        if path.startswith("/api/"):
            self.send_error(404)
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/sync":
            self._json(_safe_live_sync())
            return
        if path == "/api/refresh":
            self._json(_safe_refresh())
            return
        self.send_error(404)

    def _json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)


def run_server(host: str = "127.0.0.1", port: int = 8787) -> None:
    ensure_stats_dir()
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    # Bind immediately — never block startup on Chakra scans.
    httpd = ThreadingHTTPServer((host, port), StatsHandler)
    print(f"Prompt stats analytics -> http://{host}:{port}/", flush=True)
    print(
        "Serving ledger now; Chakra + Pi session sync runs in background / on refresh.",
        flush=True,
    )
    print(f"Ledger: {LEDGER_PATH}", flush=True)

    def _bg_sync() -> None:
        try:
            _safe_live_sync()
            print("Background session sync finished.", flush=True)
        except Exception as exc:
            print(f"Background sync failed: {exc}", flush=True)

    threading.Thread(target=_bg_sync, name="prompt-stats-sync", daemon=True).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
    finally:
        httpd.server_close()
