"""Background simulation loop.

Every tick the simulator:
  * nudges thermostat temperature/humidity toward realistic values,
  * randomly toggles camera motion events,
  * records a reading for every device into the history store,
  * evaluates automation rules (edge-triggered),
  * fires any schedules due this minute,
  * pushes device updates to WebSocket clients.
"""
from __future__ import annotations

import asyncio
import contextlib
import random
import time

from .events import bus
from .models import (
    CameraState,
    Device,
    DeviceType,
    FanState,
    LightState,
    Reading,
    Rule,
    ThermostatState,
)
from .readings_store import ReadingStore
from .store import DeviceStore, DeviceUnreachable, InvalidControl, RuleStore, ScheduleStore

# Power draw estimates (watts) for the history "power" metric.
_POWER_W = {
    DeviceType.light: 9.0,
    DeviceType.fan: 35.0,
    DeviceType.camera: 5.0,
}


class Simulator:
    def __init__(
        self,
        devices: DeviceStore,
        schedules: ScheduleStore,
        rules: RuleStore,
        readings: ReadingStore,
        interval: float = 5.0,
        seed: int | None = None,
    ) -> None:
        self.devices = devices
        self.schedules = schedules
        self.rules = rules
        self.readings = readings
        self.interval = interval
        self._random = random.Random(seed)
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _run(self) -> None:
        while True:
            await asyncio.sleep(self.interval)
            await self.tick()

    # ------------------------------------------------------------------
    async def tick(self) -> None:
        """Advance the simulation by one step (also used directly by tests)."""
        for device in self.devices.list():
            changed = self._evolve(device)
            self._record(device)
            if changed:
                await bus.publish("device_updated", device.model_dump(mode="json"))
        await self.evaluate_rules()
        await self.run_due_schedules()

    # ------------------------------------------------------------------
    def _evolve(self, device: Device) -> bool:
        """Drift sensor values in place. Returns True if anything changed."""
        state = device.state
        if isinstance(state, ThermostatState):
            before = state.model_dump()
            drift = (state.target_temp_c - state.current_temp_c) * 0.05
            if state.mode.value == "off":
                # Drift gently toward an ambient 21C when the HVAC is off.
                drift = (21.0 - state.current_temp_c) * 0.02
            noise = self._random.uniform(-0.15, 0.15)
            temp = round(state.current_temp_c + drift + noise, 2)
            humidity = round(
                min(80.0, max(20.0, state.humidity_pct + self._random.uniform(-1.0, 1.0))), 1
            )
            device.state = state.model_copy(update={"current_temp_c": temp, "humidity_pct": humidity})
            return device.state.model_dump() != before
        if isinstance(state, CameraState) and state.status.value == "online":
            motion = self._random.random() < 0.05
            if motion != state.motion_detected:
                device.state = state.model_copy(update={"motion_detected": motion})
                return True
        return False

    def _record(self, device: Device) -> None:
        state = device.state
        temp = humidity = None
        motion = None
        power = 0.0
        if isinstance(state, ThermostatState):
            temp, humidity = state.current_temp_c, state.humidity_pct
            if state.mode.value != "off":
                power = 1500.0 if abs(state.target_temp_c - state.current_temp_c) > 0.5 else 50.0
        elif isinstance(state, CameraState):
            motion = int(state.motion_detected)
            power = _POWER_W[DeviceType.camera] if state.status.value == "online" else 0.0
        elif isinstance(state, LightState):
            power = _POWER_W[DeviceType.light] * state.brightness / 100 if state.is_on else 0.0
        elif isinstance(state, FanState):
            power = _POWER_W[DeviceType.fan] * state.speed / 5 if state.is_on else 0.0
        self.readings.add(
            Reading(
                ts=time.time(),
                device_id=device.id,
                temperature_c=temp,
                humidity_pct=humidity,
                power_w=round(power, 2),
                motion=motion,
            )
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _metric_value(device: Device, metric: str) -> float | None:
        state = device.state
        if metric == "temperature" and isinstance(state, ThermostatState):
            return state.current_temp_c
        if metric == "humidity" and isinstance(state, ThermostatState):
            return state.humidity_pct
        if metric == "motion" and isinstance(state, CameraState):
            return float(state.motion_detected)
        return None

    async def evaluate_rules(self) -> list[Rule]:
        """Fire rules whose condition just became true (edge-triggered)."""
        fired: list[Rule] = []
        for rule in self.rules.list():
            if not rule.enabled:
                continue
            try:
                source = self.devices.get(rule.source_device_id)
            except KeyError:
                continue
            value = self._metric_value(source, rule.metric)
            if value is None:
                continue
            condition = (
                value > rule.threshold if rule.operator == "gt" else value < rule.threshold
            )
            if condition and not rule.triggered:
                try:
                    await self.devices.control(rule.target_device_id, rule.action)
                except (KeyError, DeviceUnreachable, InvalidControl):
                    pass  # bad target must not kill the simulation loop
                self.rules.set_triggered(rule.id, True)
                await bus.publish("rule_triggered", self.rules.get(rule.id).model_dump(mode="json"))
                fired.append(self.rules.get(rule.id))
            elif not condition and rule.triggered:
                self.rules.set_triggered(rule.id, False)
        return fired

    async def run_due_schedules(self) -> None:
        for schedule in self.schedules.due(time.time()):
            try:
                await self.devices.control(schedule.device_id, schedule.action)
            except (KeyError, DeviceUnreachable, InvalidControl):
                continue
