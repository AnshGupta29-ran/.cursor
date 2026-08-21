# EpochLedger - Security Auditor Audit Trail Export (v04_python_security-auditor_audit-trail-export)

## Overview
EpochLedger is a lightweight, offline‑first experiment‑tracking‑style service tailored for **security auditors**. It records audit‑trail events, stores them locally, and can export the trail as a CSV file. The product is **API‑only** (FastAPI) with a small CLI helper for quick interaction.

## Features
- **Local storage** – all events are kept in a JSON file under `data/audit_log.json`.
- **FastAPI** backend exposing three endpoints:
  - `POST /events` – record a new audit event.
  - `GET /events` – list all events.
  - `GET /export` – download the full audit trail as CSV.
- **CLI entry** (`scripts/cli.py`) to submit events and fetch the export without needing to start the server manually (it starts the server in the background if not running).
- **Smoke test** (`scripts/smoke.py`) that validates the end‑to‑end flow.

## Quick start
```bash
# Install fastapi and uvicorn if they are not already available
# (the environment used by the harness already provides them)

# Run the server
python -m epochledger.server &

# In another terminal, submit a sample event via the CLI
python scripts/cli.py submit "User login" "alice" "Successful login"

# Export the audit trail
python scripts/cli.py export > audit_trail.csv
```

## Running the smoke test
```bash
python scripts/smoke.py
```
The script should exit with status `0` indicating success.

## Seed data
A minimal seed file is provided under `fixtures/sample_audit.json`. The server loads this on start‑up if the persistent store does not yet exist.

## License
MIT
