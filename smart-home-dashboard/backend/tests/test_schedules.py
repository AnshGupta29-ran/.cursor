"""Schedule CRUD, validation and firing via the simulator."""
import asyncio
import time


def test_create_schedule(client, device_ids):
    payload = {
        "device_id": device_ids["Bedside Lamp"],
        "time": "07:30",
        "action": {"is_on": True, "brightness": 60},
        "days": [0, 1, 2, 3, 4],
    }
    res = client.post("/api/schedules", json=payload)
    assert res.status_code == 201
    body = res.json()
    assert body["enabled"] is True and body["days"] == [0, 1, 2, 3, 4]
    assert client.get("/api/schedules").json()[0]["id"] == body["id"]


def test_schedule_rejects_bad_time(client, device_ids):
    payload = {
        "device_id": device_ids["Bedside Lamp"],
        "time": "25:00",
        "action": {"is_on": True},
    }
    assert client.post("/api/schedules", json=payload).status_code == 422


def test_schedule_rejects_unknown_device(client):
    payload = {"device_id": "ghost", "time": "07:30", "action": {"is_on": True}}
    assert client.post("/api/schedules", json=payload).status_code == 404


def test_update_and_delete_schedule(client, device_ids):
    created = client.post(
        "/api/schedules",
        json={"device_id": device_ids["Bedroom Fan"], "time": "22:00", "action": {"is_on": False}},
    ).json()
    updated = client.patch(f"/api/schedules/{created['id']}", json={"enabled": False})
    assert updated.json()["enabled"] is False
    assert client.delete(f"/api/schedules/{created['id']}").status_code == 204
    assert client.get("/api/schedules").json() == []


def test_due_schedule_fires_action(client, device_ids):
    """A schedule for the current minute must fire exactly once."""
    lamp = device_ids["Bedside Lamp"]
    now_hhmm = time.strftime("%H:%M", time.localtime())
    client.post(
        "/api/schedules",
        json={"device_id": lamp, "time": now_hhmm, "action": {"is_on": True}},
    )

    app = client.app
    asyncio.run(app.state.simulator.run_due_schedules())
    state = client.get(f"/api/devices/{lamp}").json()["state"]
    assert state["is_on"] is True

    # Second run in the same minute must not re-fire (dedupe guard).
    client.post(f"/api/devices/{lamp}/control", json={"state": {"is_on": False}})
    asyncio.run(app.state.simulator.run_due_schedules())
    state = client.get(f"/api/devices/{lamp}").json()["state"]
    assert state["is_on"] is False
