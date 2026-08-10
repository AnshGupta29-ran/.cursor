"""Paths and schema helpers for the prompt statistics ledger."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]
STATS_DIR = REPO_ROOT / "artifacts" / "prompt_stats"
LEDGER_PATH = STATS_DIR / "ledger.jsonl"
DASHBOARD_PATH = STATS_DIR / "dashboard.html"
LATEST_PATH = STATS_DIR / "latest.json"
SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_stats_dir() -> Path:
    STATS_DIR.mkdir(parents=True, exist_ok=True)
    return STATS_DIR


def prompt_fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def record_id_for(*, source: str, key: str, fingerprint: str) -> str:
    raw = f"{source}|{key}|{fingerprint}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def append_record(record: dict[str, Any], *, dedupe: bool = True) -> bool:
    """Append one ledger row. Returns False if duplicate id skipped."""
    ensure_stats_dir()
    record = dict(record)
    record.setdefault("schema_version", SCHEMA_VERSION)
    record.setdefault("recorded_at", utc_now())
    rid = record.get("id")
    if not rid:
        raise ValueError("record requires id")
    if dedupe and LEDGER_PATH.is_file():
        for existing in iter_records():
            if existing.get("id") == rid:
                return False
    with LEDGER_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return True


def rewrite_ledger(rows: list[dict[str, Any]]) -> None:
    """Atomically replace the ledger with the given rows."""
    ensure_stats_dir()
    tmp = LEDGER_PATH.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(LEDGER_PATH)


def upsert_merge(record: dict[str, Any]) -> None:
    """Insert or shallow-merge a record by id (rewrites ledger)."""
    ensure_stats_dir()
    rid = record["id"]
    rows = list(iter_records())
    found = False
    out: list[dict[str, Any]] = []
    for row in rows:
        if row.get("id") == rid:
            merged = {**row, **record, "schema_version": SCHEMA_VERSION}
            out.append(merged)
            found = True
        else:
            out.append(row)
    if not found:
        record.setdefault("schema_version", SCHEMA_VERSION)
        record.setdefault("recorded_at", utc_now())
        out.append(record)
    rewrite_ledger(out)


def iter_records() -> Iterator[dict[str, Any]]:
    if not LEDGER_PATH.is_file():
        return
        yield  # pragma: no cover
    with LEDGER_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def load_records() -> list[dict[str, Any]]:
    return list(iter_records())
