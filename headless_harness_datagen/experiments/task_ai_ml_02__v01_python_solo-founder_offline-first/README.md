# EpochLedger – Offline‑First ML Experiment Journal (`-v01_python_solo-founder_offline-first`)

## Overview
A minimal **Python** demo that implements a tiny **MLflow‑like** experiment tracking system with the following constraints from the PRD:
* **Persistence**: local **SQLite** database (`persistence: sqlite`).
* **UI surface**: generated **static HTML** report (`ui_surface: static_html`).
* **Complexity**: medium – a few core modules, no external web framework.
* **Delivery**: a **CLI** entry point plus the HTML report (`delivery: cli_entry_plus_ui`).
* **Offline‑first**: works completely locally, no network calls.

The demo showcases the *champion‑vs‑challenger* gating workflow: an experiment can have a **champion** run; new runs are compared against it and receive a verdict (`PASS`, `REGRESSED`, `INCONCLUSIVE`).

## Project layout
```
epochledger/                # Python package
    __init__.py
    db.py                  # SQLite helper, schema creation
    experiment.py          # Data models and core logic
    cli.py                 # CLI using argparse
    ui.py                  # Simple static HTML report generator
fixtures/                  # Seed / synthetic data (CSV example)
static/                    # Generated HTML reports (git‑ignored)
scripts/smoke.py           # End‑to‑end demo script
README.md
requirements.txt          # No third‑party deps (standard library only)
```

## Quick start (smoke test)
```bash
# No external dependencies – only the Python standard library
# (requirements.txt is intentionally empty)

# Run the smoke script which exercises the full workflow
python scripts/smoke.py
```
The script will:
1. Create (or reset) `epochledger.db`.
2. Create an experiment called **demo_experiment**.
3. Start a run, log random metrics, and finish it.
4. Promote the run to **champion**.
5. Generate a static HTML report at `static/report_demo_experiment.html`.
6. Print `DONE task_ai_ml_02__v01_python_solo-founder_offline-first` and exit with code **0**.

Open the generated HTML file in any browser – it works completely offline.

## Extending the demo
* Replace the dummy metric logging in `scripts/smoke.py` with a real training loop (e.g., Scikit‑Learn).
* Add richer visualisations in `epochledger/ui.py` using Matplotlib/Plotly (still rendered to static files).
* Implement a remote sync step to back up the SQLite file for later online‑first stages.

---

**DONE** `task_ai_ml_02__v01_python_solo-founder_offline-first`
