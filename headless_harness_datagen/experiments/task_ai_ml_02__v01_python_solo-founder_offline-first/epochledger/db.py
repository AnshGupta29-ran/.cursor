import os
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "epochledger.db"


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection, creating the DB file if needed.
    The connection uses `detect_types=sqlite3.PARSE_DECLTYPES` so that Python
    ``datetime`` objects are stored as ISO strings.
    """
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the tables required for experiments, runs and metrics.
    If the tables already exist this is a no‑op.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            champion_run_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('RUNNING', 'COMPLETED')),
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP,
            params TEXT,  -- JSON string
            FOREIGN KEY (experiment_id) REFERENCES experiments(id)
        );

        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        );
        """
    )
    conn.commit()
    conn.close()

def reset_db() -> None:
    """Delete the existing DB file and recreate an empty one.
    Used by the smoke test to start from a clean state.
    """
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
