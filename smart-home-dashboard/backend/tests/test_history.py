"""Historical readings recorded by simulator ticks."""
import asyncio


def _tick(client, n=1):
    for _ in range(n):
        asyncio.run(client.app.state.simulator.tick())


def test_tick_records_readings_for_all_devices(client, device_ids):
    _tick(client, 2)
    readings = client.get(f"/api/history/{device_ids['Main Thermostat']}").json()
    assert len(readings) == 2
    assert all(r["temperature_c"] is not None for r in readings)
    assert all(r["humidity_pct"] is not None for r in readings)
    # oldest first
    assert readings[0]["ts"] <= readings[1]["ts"]


def test_light_records_power(client, device_ids):
    lamp = device_ids["Ceiling Light"]  # seeded on at 80%
    _tick(client)
    reading = client.get(f"/api/history/{lamp}").json()[0]
    assert reading["power_w"] > 0

    client.post(f"/api/devices/{lamp}/control", json={"state": {"is_on": False}})
    _tick(client)
    reading = client.get(f"/api/history/{lamp}").json()[-1]
    assert reading["power_w"] == 0


def test_history_time_range_filter(client, device_ids):
    _tick(client, 3)
    thermo = device_ids["Main Thermostat"]
    all_readings = client.get(f"/api/history/{thermo}").json()
    mid_ts = all_readings[1]["ts"]
    ranged = client.get(f"/api/history/{thermo}", params={"start": mid_ts}).json()
    assert len(ranged) == 2
    assert all(r["ts"] >= mid_ts for r in ranged)


def test_history_limit(client, device_ids):
    _tick(client, 4)
    thermo = device_ids["Main Thermostat"]
    readings = client.get(f"/api/history/{thermo}", params={"limit": 2}).json()
    assert len(readings) == 2


def test_history_unknown_device_404(client):
    assert client.get("/api/history/ghost").status_code == 404


def test_temperature_drifts_toward_target(client, device_ids):
    thermo = device_ids["Main Thermostat"]
    client.post(f"/api/devices/{thermo}/control", json={"state": {"target_temp_c": 26.0}})
    before = client.get(f"/api/devices/{thermo}").json()["state"]["current_temp_c"]
    _tick(client, 5)
    after = client.get(f"/api/devices/{thermo}").json()["state"]["current_temp_c"]
    assert after > before  # warming toward the higher target
