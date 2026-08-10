"""Docs, OpenAPI schema, health check, and the websocket stream."""
import asyncio
import json


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_openapi_schema_lists_resources(client):
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    for prefix in ("/api/devices", "/api/schedules", "/api/rules", "/api/history"):
        assert any(p.startswith(prefix) for p in paths)
    assert schema["info"]["title"] == "Smart Home Dashboard API"


def test_swagger_docs_served(client):
    res = client.get("/docs")
    assert res.status_code == 200
    assert "swagger" in res.text.lower()


def test_websocket_snapshot_and_updates(client, device_ids):
    lamp = device_ids["Floor Lamp"]
    with client.websocket_connect("/ws") as ws:
        first = json.loads(ws.receive_text())
        assert first["type"] == "snapshot"
        assert len(first["data"]) == 10

        # A control call elsewhere must be pushed to the socket.
        asyncio.run(client.app.state.devices.control(lamp, {"is_on": True}))
        event = json.loads(ws.receive_text())
        assert event["type"] == "device_updated"
        assert event["data"]["id"] == lamp
        assert event["data"]["state"]["is_on"] is True
