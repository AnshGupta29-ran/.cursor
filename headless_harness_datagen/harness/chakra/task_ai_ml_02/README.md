# EpochLedger — Offline-First ML Experiment Journal

Champion/challenger promotion gates for solo ML practitioners. **Fully offline** — no accounts, no cloud calls, no model downloads. All state lives in process memory.

## One-command startup

```bash
# Unix / Git Bash
./dev.sh

# Windows
dev.bat
```

Then open **http://127.0.0.1:5173** and click **"Seed demo: sentiment-sweep"**.

Manual startup (two terminals):

```bash
pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8000     # API

cd client && npm install && npm run dev                     # SPA on :5173
```

## Memory-only persistence

**All state is wiped on restart.** Experiments, runs, artifacts, and the API activity log live only in Python process memory — no SQLite, no disk writes. The UI shows a persistent badge ("In-memory workspace — resets on restart"). Restart the server, then re-seed.

## Demo walkthrough (UI)

1. **Experiments** → click *Seed demo: sentiment-sweep* → 8 deterministic sweep runs appear with a pinned champion (lr=0.01).
2. Read the **verdict cards** on the runs table — each finished run gets a PASS / REGRESSED / INCONCLUSIVE chip with a plain-English summary.
3. Tick up to 4 runs → **Compare selected** → param differences highlighted, metric deltas vs champion, overlaid curves.
4. Open a run → **metric curves with instability flags** (runs 2 and 5 have injected spikes), params, artifacts.
5. **Upload** a classification report → **Preview** it in-browser → **Download** round-trips.
6. **Parameter influence** panel ranks the top-3 knobs (learning_rate dominates).
7. **API Activity** (top nav) shows the last 100 requests with status and latency.

## curl walkthrough (API happy path)

```bash
# create experiment
EXP=$(curl -s -X POST http://127.0.0.1:8000/api/experiments \
  -H 'Content-Type: application/json' -d '{"name":"my-sweep"}' | python -c "import sys,json;print(json.load(sys.stdin)['id'])")

# seed first, or pin a champion on your own experiment:
curl -s -X POST http://127.0.0.1:8000/api/demo/seed

# start a run
RUN=$(curl -s -X POST http://127.0.0.1:8000/api/runs \
  -H 'Content-Type: application/json' \
  -d "{\"experiment_id\":\"$EXP\",\"name\":\"trial-1\"}" | python -c "import sys,json;print(json.load(sys.stdin)['id'])")

# log params + metric points
curl -s -X POST http://127.0.0.1:8000/api/runs/$RUN/log-batch \
  -H 'Content-Type: application/json' \
  -d '{"params":{"learning_rate":0.01},"metrics":{"f1":[{"step":0,"value":0.83}]}}'

# finish
curl -s -X POST http://127.0.0.1:8000/api/runs/$RUN/finish

# verdict (INCONCLUSIVE until a champion is pinned on this experiment)
curl -s http://127.0.0.1:8000/api/runs/$RUN/verdict
```

## Endpoint table

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | liveness |
| POST | `/api/experiments` | create experiment (name, optional gate_policy) |
| GET | `/api/experiments` | list experiments |
| GET | `/api/experiments/{id}` | experiment + runs |
| PUT | `/api/experiments/{id}/champion` | pin champion run + gate policy |
| DELETE | `/api/experiments/{id}/runs/{rid}` | delete run (deleting champion clears the gate) |
| GET | `/api/experiments/{id}/compare?run_ids=a,b,c` | side-by-side compare (≤4) |
| GET | `/api/experiments/{id}/influence` | top-3 param drivers (rank correlation) |
| POST | `/api/runs` | start run |
| POST | `/api/runs/{id}/log-batch` | log params + metric points |
| POST | `/api/runs/{id}/finish` / `/fail` | transition run |
| POST | `/api/runs/{id}/tags` | set tags |
| GET | `/api/runs/{id}` | run detail + curve instability notes |
| GET | `/api/runs/{id}/verdict` | PASS / REGRESSED / INCONCLUSIVE + summary |
| POST | `/api/runs/{id}/artifacts?name=&content_type=` | upload (raw body, ≤1MB) |
| GET | `/api/runs/{id}/artifacts` | list |
| GET | `/api/artifacts/{aid}` | download |
| GET | `/api/artifacts/{aid}/preview` | in-browser text/JSON/CSV preview |
| GET | `/api/activity` | last 100 API calls |
| POST | `/api/demo/seed` | deterministic `sentiment-sweep` seed (idempotent) |

All errors use the envelope `{"error": {"code", "message"}}`. Logging to a FINISHED run → `409`; NaN/inf metric → `422`; unknown ids → `404`; oversize artifact → `413`.

## Integrate from a training script

```python
import requests
API = "http://127.0.0.1:8000/api"
run = requests.post(f"{API}/runs", json={"experiment_id": EXP_ID, "name": "epoch-3"}).json()
requests.post(f"{API}/runs/{run['id']}/log-batch", json={"params": {"lr": 0.01}, "metrics": {"f1": [{"step": 0, "value": 0.84}]}})
requests.post(f"{API}/runs/{run['id']}/finish")
```

## Tests

```bash
pip install pytest
python -m pytest test_app.py -q     # unit: verdicts, rank correlation, instability, validation
python scripts/smoke.py             # boots server on :8765, full happy path, exits 0 on PASS
```

Everything is offline and deterministic — no network, GPUs, or model weights.

## Limitations

- **Memory-only**: restart wipes everything (by design).
- Single process, single local user — **no auth**.
- Artifact previews are text/JSON/CSV only; caps 1MB per artifact, 25MB per run.
- Not a model registry or serving layer — this is intentionally not full MLflow.
