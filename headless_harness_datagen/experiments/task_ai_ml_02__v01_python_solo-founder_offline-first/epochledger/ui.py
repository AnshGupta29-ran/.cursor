"""Utility to generate a static HTML report for an experiment.
The report is deliberately simple – a single page with tables of runs and
metrics – to satisfy the `static_html` UI surface requirement without any
external dependencies.
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any

from .db import get_connection


def _dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> Dict[str, Any]:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def _fetch_experiment(conn: sqlite3.Connection, name: str) -> Dict[str, Any]:
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    cur.execute("SELECT * FROM experiments WHERE name = ?", (name,))
    exp = cur.fetchone()
    if not exp:
        raise ValueError(f"Experiment {name!r} not found")
    return exp


def _fetch_runs(conn: sqlite3.Connection, experiment_id: int) -> List[Dict[str, Any]]:
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM runs WHERE experiment_id = ? ORDER BY started_at",
        (experiment_id,)
    )
    return cur.fetchall()


def _fetch_metrics(conn: sqlite3.Connection, run_id: int) -> List[Dict[str, Any]]:
    conn.row_factory = _dict_factory
    cur = conn.cursor()
    cur.execute(
        "SELECT key, value, timestamp FROM metrics WHERE run_id = ? ORDER BY timestamp",
        (run_id,)
    )
    return cur.fetchall()


def generate_report(experiment_name: str, output_path: Path | str) -> Path:
    """Generate a static HTML report for *experiment_name*.
    The report is written to *output_path* (a ``Path`` or string). The function
    returns the final ``Path`` object.
    """
    conn = get_connection()
    exp = _fetch_experiment(conn, experiment_name)
    runs = _fetch_runs(conn, exp["id"])
    # Build simple HTML
    html_parts: List[str] = []
    html_parts.append("<html><head><title>EpochLedger Report</title></head><body>")
    html_parts.append(f"<h1>Experiment: {experiment_name}</h1>")
    if exp.get("champion_run_id"):
        html_parts.append(f"<p><strong>Champion Run ID:</strong> {exp['champion_run_id']}</p>")
    else:
        html_parts.append("<p><strong>Champion Run ID:</strong> None</p>")
    # Table of runs
    html_parts.append("<h2>Runs</h2>")
    html_parts.append("<table border='1' cellpadding='4' cellspacing='0'>")
    html_parts.append(
        "<tr><th>Run ID</th><th>Name</th><th>Status</th><th>Started</th><th>Finished</th><th>Params</th></tr>"
    )
    for run in runs:
        params = json.loads(run["params"]) if run["params"] else {}
        html_parts.append(
            f"<tr><td>{run['id']}</td><td>{run['name']}</td><td>{run['status']}</td>"
            f"<td>{run['started_at']}</td><td>{run['finished_at'] or ''}</td><td>{json.dumps(params)}</td></tr>"
        )
    html_parts.append("</table>")
    # Metrics per run
    html_parts.append("<h2>Metrics</h2>")
    for run in runs:
        metrics = _fetch_metrics(conn, run["id"])
        if not metrics:
            continue
        html_parts.append(f"<h3>Run {run['id']} – {run['name']}</h3>")
        html_parts.append("<table border='1' cellpadding='4' cellspacing='0'>")
        html_parts.append("<tr><th>Key</th><th>Value</th><th>Timestamp</th></tr>")
        for m in metrics:
            html_parts.append(
                f"<tr><td>{m['key']}</td><td>{m['value']:.2f}</td><td>{m['timestamp']}</td></tr>"
            )
        html_parts.append("</table>")
    html_parts.append("</body></html>")
    conn.close()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(html_parts), encoding="utf-8")
    return output_path
