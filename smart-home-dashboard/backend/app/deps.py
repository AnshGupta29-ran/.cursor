"""Shared FastAPI dependencies (stores live on app.state)."""
from __future__ import annotations

from fastapi import Request

from .readings_store import ReadingStore
from .store import DeviceStore, RuleStore, ScheduleStore


def get_device_store(request: Request) -> DeviceStore:
    return request.app.state.devices


def get_schedule_store(request: Request) -> ScheduleStore:
    return request.app.state.schedules


def get_rule_store(request: Request) -> RuleStore:
    return request.app.state.rules


def get_reading_store(request: Request) -> ReadingStore:
    return request.app.state.readings
