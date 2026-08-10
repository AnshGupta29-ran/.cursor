"""Scheduled device actions."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_device_store, get_schedule_store
from ..models import Schedule, ScheduleCreate, ScheduleUpdate
from ..store import DeviceNotFound, DeviceStore, ScheduleStore

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


@router.get("", response_model=list[Schedule], summary="List schedules")
def list_schedules(store: ScheduleStore = Depends(get_schedule_store)) -> list[Schedule]:
    return store.list()


@router.post("", response_model=Schedule, status_code=201, summary="Create a schedule")
def create_schedule(
    payload: ScheduleCreate,
    store: ScheduleStore = Depends(get_schedule_store),
    devices: DeviceStore = Depends(get_device_store),
) -> Schedule:
    try:
        devices.get(payload.device_id)
    except DeviceNotFound:
        raise HTTPException(status_code=404, detail="Target device not found")
    return store.create(payload)


@router.patch("/{schedule_id}", response_model=Schedule, summary="Update a schedule")
def update_schedule(
    schedule_id: str,
    payload: ScheduleUpdate,
    store: ScheduleStore = Depends(get_schedule_store),
) -> Schedule:
    try:
        return store.update(schedule_id, payload)
    except DeviceNotFound:
        raise HTTPException(status_code=404, detail="Schedule not found")


@router.delete("/{schedule_id}", status_code=204, summary="Delete a schedule")
def delete_schedule(
    schedule_id: str, store: ScheduleStore = Depends(get_schedule_store)
) -> None:
    try:
        store.delete(schedule_id)
    except DeviceNotFound:
        raise HTTPException(status_code=404, detail="Schedule not found")
