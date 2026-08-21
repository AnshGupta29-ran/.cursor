import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import csv
from io import StringIO

app = FastAPI()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
STORE_PATH = os.path.join(DATA_DIR, "audit_log.json")
FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_audit.json")

if not os.path.isdir(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

# Load existing store or seed from fixture
if os.path.isfile(STORE_PATH):
    with open(STORE_PATH, "r", encoding="utf-8") as f:
        _store = json.load(f)
else:
    if os.path.isfile(FIXTURE_PATH):
        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            _store = json.load(f)
    else:
        _store = []
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(_store, f, indent=2)

def _save_store():
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(_store, f, indent=2)

class AuditEvent(BaseModel):
    title: str
    user: str
    description: str
    timestamp: str | None = None  # optional iso timestamp, server will fill if missing

@app.get("/events")
def list_events():
    return _store

@app.post("/events")
def create_event(event: AuditEvent):
    import datetime
    ev = event.dict()
    if not ev.get("timestamp"):
        ev["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
    _store.append(ev)
    _save_store()
    return {"status": "ok", "event": ev}

@app.get("/export")
def export_csv():
    if not _store:
        raise HTTPException(status_code=404, detail="No events recorded")
    def generate():
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=["timestamp", "title", "user", "description"])
        writer.writeheader()
        for ev in _store:
            writer.writerow({
                "timestamp": ev.get("timestamp", ""),
                "title": ev.get("title", ""),
                "user": ev.get("user", ""),
                "description": ev.get("description", ""),
            })
            data = output.getvalue()
            output.seek(0)
            output.truncate(0)
            yield data
    return StreamingResponse(generate(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=audit_log.csv"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
