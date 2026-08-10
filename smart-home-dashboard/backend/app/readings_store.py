"""SQLite-backed store for historical sensor readings."""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Optional

from .models import Reading

_SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    ts REAL NOT NULL,
    device_id TEXT NOT NULL,
    temperature_c REAL,
    humidity_pct REAL,
    power_w REAL,
    motion INTEGER
);
CREATE INDEX IF NOT EXISTS idx_readings_device_ts ON readings (device_id, ts);
"""


class ReadingStore:
    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    def add(self, reading: Reading) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO readings VALUES (?, ?, ?, ?, ?, ?)",
                (
                    reading.ts,
                    reading.device_id,
                    reading.temperature_c,
                    reading.humidity_pct,
                    reading.power_w,
                    reading.motion,
                ),
            )
            self._conn.commit()

    def query(
        self,
        device_id: str,
        start: Optional[float] = None,
        end: Optional[float] = None,
        limit: int = 500,
    ) -> list[Reading]:
        sql = "SELECT ts, device_id, temperature_c, humidity_pct, power_w, motion FROM readings WHERE device_id = ?"
        params: list = [device_id]
        if start is not None:
            sql += " AND ts >= ?"
            params.append(start)
        if end is not None:
            sql += " AND ts <= ?"
            params.append(end)
        sql += " ORDER BY ts DESC LIMIT ?"
        params.append(limit)
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [Reading(**dict(zip(
            ("ts", "device_id", "temperature_c", "humidity_pct", "power_w", "motion"), row
        ))) for row in reversed(rows)]

    def close(self) -> None:
        with self._lock:
            self._conn.close()
