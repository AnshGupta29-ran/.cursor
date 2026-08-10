"""In-memory stores for devices, schedules, and automation rules."""
from __future__ import annotations

import threading
import time
from typing import Iterable, Optional

from pydantic import ValidationError

from .events import bus
from .models import (
    CameraState,
    Device,
    DeviceCreate,
    DeviceState,
    DeviceType,
    DeviceUpdate,
    DoorState,
    FanState,
    LightState,
    Rule,
    RuleCreate,
    RuleUpdate,
    Schedule,
    ScheduleCreate,
    ScheduleUpdate,
    ThermostatState,
    new_id,
)

_STATE_MODELS: dict[DeviceType, type] = {
    DeviceType.light: LightState,
    DeviceType.fan: FanState,
    DeviceType.thermostat: ThermostatState,
    DeviceType.door: DoorState,
    DeviceType.camera: CameraState,
}


class DeviceNotFound(KeyError):
    pass


class DeviceUnreachable(RuntimeError):
    pass


class InvalidControl(ValueError):
    pass


def _seed_devices() -> list[Device]:
    """A plausible starter home: two floors, six rooms, ten devices."""
    seeds: list[tuple[str, str, DeviceType, DeviceState]] = [
        ("Ceiling Light", "Living Room", DeviceType.light, LightState(is_on=True, brightness=80, color_temp_k=3000)),
        ("Floor Lamp", "Living Room", DeviceType.light, LightState()),
        ("Ceiling Fan", "Living Room", DeviceType.fan, FanState(is_on=True, speed=2)),
        ("Main Thermostat", "Hallway", DeviceType.thermostat, ThermostatState()),
        ("Front Door", "Entrance", DeviceType.door, DoorState(is_open=False, is_locked=True)),
        ("Porch Camera", "Entrance", DeviceType.camera, CameraState(is_recording=True)),
        ("Bedside Lamp", "Bedroom", DeviceType.light, LightState()),
        ("Bedroom Fan", "Bedroom", DeviceType.fan, FanState()),
        ("Bedroom Thermostat", "Bedroom", DeviceType.thermostat, ThermostatState(current_temp_c=20.2, target_temp_c=19.5)),
        ("Back Door", "Kitchen", DeviceType.door, DoorState(is_open=False, is_locked=False)),
    ]
    now = time.time()
    return [
        Device(id=new_id(), name=name, room=room, type=type_, state=state, updated_at=now)
        for name, room, type_, state in seeds
    ]


class DeviceStore:
    def __init__(self, seed: bool = True) -> None:
        self._lock = threading.RLock()
        self._devices: dict[str, Device] = {}
        if seed:
            for device in _seed_devices():
                self._devices[device.id] = device

    # -- queries ----------------------------------------------------------
    def list(self, room: Optional[str] = None, type_: Optional[DeviceType] = None) -> list[Device]:
        with self._lock:
            devices = list(self._devices.values())
        if room is not None:
            devices = [d for d in devices if d.room.lower() == room.lower()]
        if type_ is not None:
            devices = [d for d in devices if d.type == type_]
        return devices

    def get(self, device_id: str) -> Device:
        with self._lock:
            device = self._devices.get(device_id)
        if device is None:
            raise DeviceNotFound(device_id)
        return device

    def rooms(self) -> list[str]:
        with self._lock:
            return sorted({d.room for d in self._devices.values()})

    # -- mutations --------------------------------------------------------
    def create(self, payload: DeviceCreate) -> Device:
        device = Device(
            id=new_id(),
            name=payload.name,
            room=payload.room,
            type=payload.type,
            state=_STATE_MODELS[payload.type](),
            updated_at=time.time(),
        )
        with self._lock:
            self._devices[device.id] = device
        return device

    def update_meta(self, device_id: str, payload: DeviceUpdate) -> Device:
        with self._lock:
            device = self.get(device_id)
            updates = payload.model_dump(exclude_none=True)
            if updates:
                device = device.model_copy(update={**updates, "updated_at": time.time()})
                self._devices[device_id] = device
        return device

    def delete(self, device_id: str) -> Device:
        with self._lock:
            device = self._devices.pop(device_id, None)
        if device is None:
            raise DeviceNotFound(device_id)
        return device

    async def control(self, device_id: str, changes: dict) -> Device:
        """Apply a partial state update, validated against the device type."""
        with self._lock:
            device = self.get(device_id)
            if not device.reachable:
                raise DeviceUnreachable(f"{device.name} is offline")
            state_model = _STATE_MODELS[device.type]
            unknown = set(changes) - set(state_model.model_fields)
            if unknown:
                raise InvalidControl(
                    f"{device.type.value} has no state field(s): {', '.join(sorted(unknown))}"
                )
            try:
                new_state = state_model(**{**device.state.model_dump(), **changes})
            except ValidationError as exc:
                raise InvalidControl(exc.errors()[0]["msg"]) from exc
            device = device.model_copy(update={"state": new_state, "updated_at": time.time()})
            self._devices[device_id] = device
        await bus.publish("device_updated", device.model_dump(mode="json"))
        return device


class ScheduleStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._schedules: dict[str, Schedule] = {}
        self._last_fired: dict[str, str] = {}  # schedule_id -> "YYYY-MM-DD HH:MM"

    def list(self) -> list[Schedule]:
        with self._lock:
            return list(self._schedules.values())

    def get(self, schedule_id: str) -> Schedule:
        with self._lock:
            schedule = self._schedules.get(schedule_id)
        if schedule is None:
            raise DeviceNotFound(schedule_id)
        return schedule

    def create(self, payload: ScheduleCreate) -> Schedule:
        schedule = Schedule(id=new_id(), **payload.model_dump())
        with self._lock:
            self._schedules[schedule.id] = schedule
        return schedule

    def update(self, schedule_id: str, payload: ScheduleUpdate) -> Schedule:
        with self._lock:
            schedule = self.get(schedule_id)
            updates = payload.model_dump(exclude_none=True)
            if updates:
                schedule = schedule.model_copy(update=updates)
                self._schedules[schedule_id] = schedule
        return schedule

    def delete(self, schedule_id: str) -> None:
        with self._lock:
            if self._schedules.pop(schedule_id, None) is None:
                raise DeviceNotFound(schedule_id)
            self._last_fired.pop(schedule_id, None)

    def due(self, now: float) -> Iterable[Schedule]:
        """Schedules matching the current minute that haven't fired yet."""
        local = time.localtime(now)
        hhmm = time.strftime("%H:%M", local)
        stamp = time.strftime("%Y-%m-%d %H:%M", local)
        weekday = local.tm_wday
        with self._lock:
            schedules = list(self._schedules.values())
        for s in schedules:
            if not s.enabled or s.time != hhmm:
                continue
            if s.days and weekday not in s.days:
                continue
            if self._last_fired.get(s.id) == stamp:
                continue
            with self._lock:
                self._last_fired[s.id] = stamp
            yield s


class RuleStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._rules: dict[str, Rule] = {}

    def list(self) -> list[Rule]:
        with self._lock:
            return list(self._rules.values())

    def get(self, rule_id: str) -> Rule:
        with self._lock:
            rule = self._rules.get(rule_id)
        if rule is None:
            raise DeviceNotFound(rule_id)
        return rule

    def create(self, payload: RuleCreate) -> Rule:
        rule = Rule(id=new_id(), **payload.model_dump())
        with self._lock:
            self._rules[rule.id] = rule
        return rule

    def update(self, rule_id: str, payload: RuleUpdate) -> Rule:
        with self._lock:
            rule = self.get(rule_id)
            updates = payload.model_dump(exclude_none=True)
            if updates:
                rule = rule.model_copy(update=updates)
                self._rules[rule_id] = rule
        return rule

    def delete(self, rule_id: str) -> None:
        with self._lock:
            if self._rules.pop(rule_id, None) is None:
                raise DeviceNotFound(rule_id)

    def set_triggered(self, rule_id: str, triggered: bool) -> None:
        with self._lock:
            rule = self._rules.get(rule_id)
            if rule is not None:
                self._rules[rule_id] = rule.model_copy(update={"triggered": triggered})
