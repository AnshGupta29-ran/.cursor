import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client():
    # simulate=False keeps tests deterministic: the background tick is
    # disabled and tests drive the simulator explicitly when needed.
    app = create_app(db_path=":memory:", simulate=False)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def device_ids(client):
    """Map of device name -> id for the seeded home."""
    devices = client.get("/api/devices").json()
    return {d["name"]: d["id"] for d in devices}
