# Smart Home Dashboard

Full-stack smart home simulator: **FastAPI** backend + **React / TypeScript** frontend.

- Simulated lights, fans, thermostats, doors and cameras with per-type state validation
- Real-time updates over WebSocket (no polling)
- Schedules (time-of-day + weekday actions) and edge-triggered automation rules
- Historical sensor data (temperature / humidity / power / motion) persisted to SQLite and charted in the UI
- Interactive API docs (Swagger UI) and a pytest suite for the backend

## Quick start

### Backend (port 8000)

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate          # Windows; use source .venv/bin/activate on POSIX
pip install -r requirements.txt
python run.py
```

### Frontend (port 5173)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — Vite proxies `/api` and `/ws` to the backend.

## API overview

Interactive docs: **http://localhost:8000/docs** (Swagger UI) or `/redoc`.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/devices` | List devices (filters: `room`, `type`) |
| POST | `/api/devices` | Add a device |
| GET | `/api/devices/rooms` | List room names |
| GET / PATCH / DELETE | `/api/devices/{id}` | Fetch / rename / remove a device |
| POST | `/api/devices/{id}/control` | Apply a partial state update |
| GET / POST | `/api/schedules` | List / create schedules |
| PATCH / DELETE | `/api/schedules/{id}` | Update / delete a schedule |
| GET / POST | `/api/rules` | List / create automation rules |
| PATCH / DELETE | `/api/rules/{id}` | Update / delete a rule |
| GET | `/api/history/{device_id}` | Historical readings (`start`, `end`, `limit`) |
| GET | `/api/health` | Health check |
| WS | `/ws` | Event stream: `snapshot`, `device_updated`, `rule_triggered` |

### Controlling a device

`POST /api/devices/{id}/control` with a partial state object — fields are
validated against the device type:

```json
{ "state": { "is_on": true, "brightness": 60 } }
```

| Type | State fields |
| --- | --- |
| light | `is_on`, `brightness` (0–100), `color_temp_k` (2200–6500) |
| fan | `is_on`, `speed` (1–5) |
| thermostat | `target_temp_c` (10–32), `mode` (`heat`/`cool`/`auto`/`off`); `current_temp_c`/`humidity_pct` are simulated |
| door | `is_open`, `is_locked` |
| camera | `is_recording`, `status` (`online`/`offline`); `motion_detected` is simulated |

Unknown fields return `400`; an offline camera returns `409`.

### Schedules

```json
{
  "device_id": "<id>",
  "time": "07:30",
  "days": [0, 1, 2, 3, 4],
  "action": { "is_on": true, "brightness": 60 }
}
```

`days` is 0=Monday … 6=Sunday (empty = every day). A schedule fires at most
once per minute on the simulator tick.

### Automation rules

WHEN a sensor crosses a threshold THEN apply an action — edge-triggered, so a
rule fires once per crossing and re-arms when the sensor returns to normal.

```json
{
  "name": "Too warm → bedroom fan",
  "source_device_id": "<thermostat id>",
  "metric": "temperature",
  "operator": "gt",
  "threshold": 26,
  "target_device_id": "<fan id>",
  "action": { "is_on": true, "speed": 4 }
}
```

`metric` is `temperature`/`humidity` (thermostats) or `motion` (cameras).

## Simulation loop

Every 5 s the backend drifts temperatures/humidity toward targets, flips
random camera motion events, records a reading per device into SQLite,
evaluates rules, fires due schedules, and broadcasts changes over `/ws`.

## Tests

```bash
cd backend
.venv/Scripts/python -m pytest -v
```

Covers device CRUD + control validation, schedule validation/firing/dedupe,
rule validation/edge-triggering/disabling, history recording + filtering, and
docs/websocket endpoints.
