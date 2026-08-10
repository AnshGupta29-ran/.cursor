"""Domain models for the smart home simulation.

Each device type has its own state model so Pydantic can validate
control payloads per type (e.g. rejecting out-of-range temperatures).
"""
from __future__ import annotations

import uuid
from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


class DeviceType(str, Enum):
    light = "light"
    fan = "fan"
    thermostat = "thermostat"
    door = "door"
    camera = "camera"


class ThermostatMode(str, Enum):
    heat = "heat"
    cool = "cool"
    auto = "auto"
    off = "off"


class CameraStatus(str, Enum):
    online = "online"
    offline = "offline"


# ---------------------------------------------------------------------------
# Device states
# ---------------------------------------------------------------------------

class LightState(BaseModel):
    is_on: bool = False
    brightness: int = Field(default=100, ge=0, le=100)
    color_temp_k: int = Field(default=4000, ge=2200, le=6500)


class FanState(BaseModel):
    is_on: bool = False
    speed: int = Field(default=2, ge=1, le=5)


class ThermostatState(BaseModel):
    current_temp_c: float = 21.5
    target_temp_c: float = Field(default=21.0, ge=10.0, le=32.0)
    humidity_pct: float = Field(default=45.0, ge=0.0, le=100.0)
    mode: ThermostatMode = ThermostatMode.auto


class DoorState(BaseModel):
    is_open: bool = False
    is_locked: bool = True


class CameraState(BaseModel):
    is_recording: bool = False
    motion_detected: bool = False
    status: CameraStatus = CameraStatus.online


DeviceState = Union[LightState, FanState, ThermostatState, DoorState, CameraState]


# ---------------------------------------------------------------------------
# Devices
# ---------------------------------------------------------------------------

class DeviceBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    room: str = Field(min_length=1, max_length=80)


class DeviceCreate(DeviceBase):
    type: DeviceType


class Device(DeviceBase):
    id: str
    type: DeviceType
    state: DeviceState
    updated_at: float

    @property
    def reachable(self) -> bool:
        """Offline cameras refuse commands."""
        return not (
            self.type == DeviceType.camera
            and isinstance(self.state, CameraState)
            and self.state.status == CameraStatus.offline
        )


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    room: Optional[str] = Field(default=None, min_length=1, max_length=80)


class ControlRequest(BaseModel):
    """Partial state update; keys are validated against the device type."""

    state: dict


# ---------------------------------------------------------------------------
# Schedules
# ---------------------------------------------------------------------------

class ScheduleBase(BaseModel):
    device_id: str
    time: str = Field(
        pattern=r"^([01]\d|2[0-3]):[0-5]\d$",
        description="Local wall-clock time, HH:MM (24h).",
    )
    action: dict
    days: list[int] = Field(
        default_factory=lambda: list(range(7)),
        description="Days of week, 0=Monday .. 6=Sunday. Empty means every day.",
    )
    enabled: bool = True


class ScheduleCreate(ScheduleBase):
    pass


class Schedule(ScheduleBase):
    id: str


class ScheduleUpdate(BaseModel):
    time: Optional[str] = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    action: Optional[dict] = None
    days: Optional[list[int]] = None
    enabled: Optional[bool] = None


# ---------------------------------------------------------------------------
# Automation rules
# ---------------------------------------------------------------------------

Metric = Literal["temperature", "humidity", "motion"]
Operator = Literal["gt", "lt"]


class RuleBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    source_device_id: str
    metric: Metric
    operator: Operator
    threshold: float
    target_device_id: str
    action: dict
    enabled: bool = True


class RuleCreate(RuleBase):
    pass


class Rule(RuleBase):
    id: str
    triggered: bool = False  # edge detection: only fire on crossing the threshold


class RuleUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    operator: Optional[Operator] = None
    threshold: Optional[float] = None
    action: Optional[dict] = None
    enabled: Optional[bool] = None


# ---------------------------------------------------------------------------
# Historical readings
# ---------------------------------------------------------------------------

class Reading(BaseModel):
    ts: float
    device_id: str
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    power_w: Optional[float] = None
    motion: Optional[int] = None


def new_id() -> str:
    return uuid.uuid4().hex[:12]
