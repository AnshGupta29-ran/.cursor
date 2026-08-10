"""Device listing, filtering, CRUD and control validation."""

ALL_TYPES = {"light", "fan", "thermostat", "door", "camera"}


def test_seeded_devices_cover_all_types(client):
    devices = client.get("/api/devices").json()
    assert len(devices) == 10
    assert {d["type"] for d in devices} == ALL_TYPES


def test_filter_by_type(client):
    devices = client.get("/api/devices", params={"type": "light"}).json()
    assert devices and all(d["type"] == "light" for d in devices)


def test_filter_by_room_case_insensitive(client):
    devices = client.get("/api/devices", params={"room": "bedroom"}).json()
    assert devices and all(d["room"] == "Bedroom" for d in devices)


def test_rooms_endpoint(client):
    rooms = client.get("/api/devices/rooms").json()
    assert rooms == sorted(rooms)
    assert "Living Room" in rooms


def test_get_device_404(client):
    assert client.get("/api/devices/nope").status_code == 404


def test_create_and_delete_device(client):
    payload = {"name": "Desk Lamp", "room": "Office", "type": "light"}
    created = client.post("/api/devices", json=payload)
    assert created.status_code == 201
    device = created.json()
    assert device["state"] == {"is_on": False, "brightness": 100, "color_temp_k": 4000}

    assert client.delete(f"/api/devices/{device['id']}").status_code == 204
    assert client.get(f"/api/devices/{device['id']}").status_code == 404


def test_rename_device(client, device_ids):
    lamp = device_ids["Floor Lamp"]
    res = client.patch(f"/api/devices/{lamp}", json={"name": "Reading Lamp"})
    assert res.status_code == 200
    assert res.json()["name"] == "Reading Lamp"


# -- control -----------------------------------------------------------------

def test_control_light(client, device_ids):
    lamp = device_ids["Floor Lamp"]
    res = client.post(
        f"/api/devices/{lamp}/control",
        json={"state": {"is_on": True, "brightness": 42}},
    )
    assert res.status_code == 200
    state = res.json()["state"]
    assert state["is_on"] is True and state["brightness"] == 42


def test_control_rejects_out_of_range_value(client, device_ids):
    lamp = device_ids["Floor Lamp"]
    res = client.post(f"/api/devices/{lamp}/control", json={"state": {"brightness": 500}})
    assert res.status_code == 400


def test_control_rejects_unknown_field(client, device_ids):
    lamp = device_ids["Floor Lamp"]
    res = client.post(f"/api/devices/{lamp}/control", json={"state": {"speed": 3}})
    assert res.status_code == 400
    assert "speed" in res.json()["detail"]


def test_control_thermostat_mode_and_target(client, device_ids):
    thermo = device_ids["Main Thermostat"]
    res = client.post(
        f"/api/devices/{thermo}/control",
        json={"state": {"mode": "cool", "target_temp_c": 18.5}},
    )
    assert res.status_code == 200
    state = res.json()["state"]
    assert state["mode"] == "cool" and state["target_temp_c"] == 18.5


def test_control_door_lock_unlock(client, device_ids):
    door = device_ids["Front Door"]
    res = client.post(f"/api/devices/{door}/control", json={"state": {"is_locked": False}})
    assert res.status_code == 200
    assert res.json()["state"]["is_locked"] is False


def test_offline_camera_is_unreachable(client, device_ids):
    cam = device_ids["Porch Camera"]
    assert client.post(
        f"/api/devices/{cam}/control", json={"state": {"status": "offline"}}
    ).status_code == 200
    res = client.post(f"/api/devices/{cam}/control", json={"state": {"is_recording": True}})
    assert res.status_code == 409
