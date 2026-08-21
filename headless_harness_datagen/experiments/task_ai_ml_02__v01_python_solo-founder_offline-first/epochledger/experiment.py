import json
import random
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from .db import get_connection

# ---------- Data helpers ----------

def _dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> Dict[str, Any]:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

# ---------- Experiment operations ----------

def create_experiment(name: str) -> int:
    """Create a new experiment and return its DB id.
    Raises sqlite3.IntegrityError if the name already exists.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO experiments (name) VALUES (?)",
        (name,)
    )
    exp_id = cur.lastrowid
    conn.commit()
    conn.close()
    return exp_id

def get_experiment_by_name(name: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    cur.execute("SELECT * FROM experiments WHERE name = ?", (name,))
    row = cur.fetchone()
    conn.close()
    return row

# ---------- Run operations ----------

def start_run(experiment_id: int, run_name: str, params: Optional[Dict[str, Any]] = None) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO runs (experiment_id, name, status, params) VALUES (?, ?, 'RUNNING', ?)",
        (experiment_id, run_name, json.dumps(params) if params else None)
    )
    run_id = cur.lastrowid
    conn.commit()
    conn.close()
    return run_id

def log_metric(run_id: int, key: str, value: float) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO metrics (run_id, key, value) VALUES (?, ?, ?)",
        (run_id, key, value)
    )
    conn.commit()
    conn.close()

def finish_run(run_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE runs SET status='COMPLETED', finished_at=? WHERE id=?",
        (datetime.utcnow(), run_id)
    )
    conn.commit()
    conn.close()

def get_latest_metrics(run_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    cur.execute(
        "SELECT key, value, timestamp FROM metrics WHERE run_id = ? ORDER BY timestamp",
        (run_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows

# ---------- Champion / challenger logic ----------

def set_champion(experiment_id: int, run_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE experiments SET champion_run_id = ? WHERE id = ?",
        (run_id, experiment_id)
    )
    conn.commit()
    conn.close()

def get_champion_run_id(experiment_id: int) -> Optional[int]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT champion_run_id FROM experiments WHERE id = ?",
        (experiment_id,)
    )
    row = cur.fetchone()
    conn.close()
    return row[0] if row and row[0] is not None else None

def compare_runs(champion_run_id: int, challenger_run_id: int) -> str:
    """Very simple comparison: if the challenger has a higher average metric value
    it *passes*, otherwise it's a *regression*.
    Returns one of ``PASS``, ``REGRESSED`` or ``INCONCLUSIVE`` (if no metrics).
    """
    champ_metrics = get_latest_metrics(champion_run_id)
    chall_metrics = get_latest_metrics(challenger_run_id)
    if not champ_metrics or not chall_metrics:
        return "INCONCLUSIVE"
    champ_avg = sum(m['value'] for m in champ_metrics) / len(champ_metrics)
    chall_avg = sum(m['value'] for m in chall_metrics) / len(chall_metrics)
    if chall_avg >= champ_avg:
        return "PASS"
    else:
        return "REGRESSED"

def challenger_flow(experiment_name: str, run_name: str, params: Optional[Dict[str, Any]] = None) -> str:
    """Convenience helper used by the smoke script.
    Creates a run, logs a few random metrics, finishes it and returns the verdict
    against the current champion (if any). If there is no champion the run is
    promoted automatically.
    """
    exp = get_experiment_by_name(experiment_name)
    if not exp:
        raise ValueError(f"Experiment {experiment_name!r} does not exist")
    exp_id = exp['id']
    run_id = start_run(exp_id, run_name, params)
    # Log 5 random metrics
    for i in range(5):
        log_metric(run_id, f"metric_{i}", random.random() * 100)
    finish_run(run_id)
    champion_id = get_champion_run_id(exp_id)
    if champion_id is None:
        set_champion(exp_id, run_id)
        return "PROMOTED_TO_CHAMPION"
    verdict = compare_runs(champion_id, run_id)
    if verdict == "PASS":
        set_champion(exp_id, run_id)
    return verdict
