"""Automation rules: validation and edge-triggered firing."""
import asyncio


def _create_rule(client, source, target, **overrides):
    payload = {
        "name": "Too warm -> fan on",
        "source_device_id": source,
        "metric": "temperature",
        "operator": "gt",
        "threshold": 25.0,
        "target_device_id": target,
        "action": {"is_on": True, "speed": 4},
    }
    payload.update(overrides)
    return client.post("/api/rules", json=payload)


def test_create_rule(client, device_ids):
    res = _create_rule(client, device_ids["Main Thermostat"], device_ids["Ceiling Fan"])
    assert res.status_code == 201
    assert res.json()["triggered"] is False


def test_rule_rejects_wrong_sensor_type(client, device_ids):
    # A light cannot report temperature.
    res = _create_rule(client, device_ids["Floor Lamp"], device_ids["Ceiling Fan"])
    assert res.status_code == 400


def test_rule_rejects_unknown_device(client, device_ids):
    res = _create_rule(client, "ghost", device_ids["Ceiling Fan"])
    assert res.status_code == 404


def test_update_and_delete_rule(client, device_ids):
    rule = _create_rule(client, device_ids["Main Thermostat"], device_ids["Ceiling Fan"]).json()
    res = client.patch(f"/api/rules/{rule['id']}", json={"threshold": 30.0, "enabled": False})
    assert res.json()["threshold"] == 30.0
    assert res.json()["enabled"] is False
    assert client.delete(f"/api/rules/{rule['id']}").status_code == 204
    assert client.get("/api/rules").json() == []


def test_rule_fires_on_threshold_crossing_only(client, device_ids):
    thermo = device_ids["Main Thermostat"]
    fan = device_ids["Bedroom Fan"]  # seeded off
    rule = _create_rule(client, thermo, fan).json()

    app = client.app
    devices = app.state.devices

    # Push temperature above the threshold and evaluate.
    device = devices.get(thermo)
    device.state = device.state.model_copy(update={"current_temp_c": 26.0})
    fired = asyncio.run(app.state.simulator.evaluate_rules())
    assert [r.id for r in fired] == [rule["id"]]
    assert client.get(f"/api/devices/{fan}").json()["state"]["is_on"] is True

    # Still above threshold: must NOT fire again (edge-triggered).
    assert asyncio.run(app.state.simulator.evaluate_rules()) == []

    # Below threshold re-arms the rule.
    device = devices.get(thermo)
    device.state = device.state.model_copy(update={"current_temp_c": 22.0})
    assert asyncio.run(app.state.simulator.evaluate_rules()) == []
    assert client.get("/api/rules").json()[0]["triggered"] is False


def test_disabled_rule_never_fires(client, device_ids):
    thermo = device_ids["Main Thermostat"]
    fan = device_ids["Bedroom Fan"]
    _create_rule(client, thermo, fan, enabled=False)
    device = client.app.state.devices.get(thermo)
    device.state = device.state.model_copy(update={"current_temp_c": 30.0})
    assert asyncio.run(client.app.state.simulator.evaluate_rules()) == []
    assert client.get(f"/api/devices/{fan}").json()["state"]["is_on"] is False


def test_motion_rule_on_camera(client, device_ids):
    cam = device_ids["Porch Camera"]
    light = device_ids["Ceiling Light"]
    res = client.post(
        "/api/rules",
        json={
            "name": "Motion -> porch light",
            "source_device_id": cam,
            "metric": "motion",
            "operator": "gt",
            "threshold": 0,
            "target_device_id": light,
            "action": {"is_on": True, "brightness": 100},
        },
    )
    assert res.status_code == 201
    camera = client.app.state.devices.get(cam)
    camera.state = camera.state.model_copy(update={"motion_detected": True})
    fired = asyncio.run(client.app.state.simulator.evaluate_rules())
    assert len(fired) == 1
    assert client.get(f"/api/devices/{light}").json()["state"]["brightness"] == 100
