"""Durable per-task checkpoint (crash-safe resume)."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from datagen_pipeline.paths import CHECKPOINT_PATH, ensure_pipeline_dirs


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


class CheckpointStore:
    """JSON checkpoint: tasks keyed by task_key → status/attempts/error."""

    def __init__(self, path: Path | None = None) -> None:
        ensure_pipeline_dirs()
        self.path = path or CHECKPOINT_PATH
        self._lock = threading.Lock()
        self._data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {
                "schema_version": 1,
                "created_at": _utc(),
                "updated_at": _utc(),
                "tasks": {},
                "meta": {},
            }
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            bak = self.path.with_suffix(".json.corrupt")
            self.path.replace(bak)
            return {
                "schema_version": 1,
                "created_at": _utc(),
                "updated_at": _utc(),
                "tasks": {},
                "meta": {"recovered_from": str(bak)},
            }

    def _save(self) -> None:
        self._data["updated_at"] = _utc()
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    def get(self, task_key: str) -> dict[str, Any] | None:
        return self._data.get("tasks", {}).get(task_key)

    def status(self, task_key: str) -> str:
        row = self.get(task_key)
        return str(row.get("status") if row else "pending")

    def upsert(self, task_key: str, **fields: Any) -> dict[str, Any]:
        with self._lock:
            tasks = self._data.setdefault("tasks", {})
            row = dict(tasks.get(task_key) or {"task_key": task_key, "attempts": 0})
            row.update(fields)
            row["updated_at"] = _utc()
            tasks[task_key] = row
            self._save()
            return row

    def mark_running(self, task_key: str, **extra: Any) -> None:
        row = self.get(task_key) or {}
        attempts = int(row.get("attempts") or 0) + 1
        self.upsert(
            task_key,
            status="running",
            attempts=attempts,
            started_at=_utc(),
            error=None,
            **extra,
        )

    def mark_done(self, task_key: str, **extra: Any) -> None:
        self.upsert(task_key, status="done", finished_at=_utc(), error=None, **extra)

    def mark_built(self, task_key: str, **extra: Any) -> None:
        """Agent finished implementing; validate/repair deferred to a later pass."""
        # Callers may pass validated=; keep a single value for upsert.
        extra.pop("validated", None)
        self.upsert(
            task_key,
            status="built",
            finished_at=_utc(),
            error=None,
            validated=False,
            **extra,
        )

    def mark_failed(self, task_key: str, error: str, **extra: Any) -> None:
        self.upsert(
            task_key,
            status="failed",
            finished_at=_utc(),
            error=(error or "")[:2000],
            **extra,
        )

    def mark_skipped(self, task_key: str, reason: str = "") -> None:
        self.upsert(task_key, status="skipped", finished_at=_utc(), error=reason or None)

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in self._data.get("tasks", {}).values():
            st = str(row.get("status") or "pending")
            counts[st] = counts.get(st, 0) + 1
        return counts

    def reset_failed(self) -> int:
        n = 0
        with self._lock:
            for key, row in list(self._data.get("tasks", {}).items()):
                if row.get("status") == "failed":
                    row["status"] = "pending"
                    row["error"] = None
                    row["updated_at"] = _utc()
                    n += 1
            if n:
                self._save()
        return n

    def reset_running(self) -> int:
        """Crash recovery: running → pending so they can retry."""
        n = 0
        with self._lock:
            for key, row in list(self._data.get("tasks", {}).items()):
                if row.get("status") == "running":
                    row["status"] = "pending"
                    row["error"] = "interrupted (was running)"
                    row["updated_at"] = _utc()
                    n += 1
            if n:
                self._save()
        return n

    def reset_built(self, keys: list[str] | None = None) -> list[str]:
        """built → pending so incomplete agent work is finished (not skipped)."""
        reset: list[str] = []
        with self._lock:
            tasks = self._data.get("tasks", {})
            targets = list(keys) if keys else [
                k for k, row in tasks.items() if row.get("status") == "built"
            ]
            for key in targets:
                row = tasks.get(key)
                if not row:
                    continue
                if row.get("status") not in ("built", "running", "failed"):
                    continue
                row["status"] = "pending"
                row["error"] = None
                row["validated"] = False
                row["note"] = "reset to pending - must complete agent run"
                row["updated_at"] = _utc()
                reset.append(key)
            if reset:
                self._save()
        return reset
