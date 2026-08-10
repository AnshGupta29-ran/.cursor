"""Device CRUD + control endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import get_device_store
from ..models import (
    ControlRequest,
    Device,
    DeviceCreate,
    DeviceType,
    DeviceUpdate,
)
from ..store import DeviceNotFound, DeviceStore, DeviceUnreachable, InvalidControl

router = APIRouter(prefix="/api/devices", tags=["devices"])

# NOTE: /rooms must be registered before /{device_id} or it would be
# captured as a device id.
@router.get("", response_model=list[Device], summary="List devices")
def list_devices(
    room: Optional[str] = Query(default=None, description="Filter by room name (case-insensitive)"),
    type: Optional[DeviceType] = Query(default=None, description="Filter by device type"),
    store: DeviceStore = Depends(get_device_store),
) -> list[Device]:
    return store.list(room=room, type_=type)


@router.get("/rooms", response_model=list[str], summary="List rooms")
def list_rooms(store: DeviceStore = Depends(get_device_store)) -> list[str]:
    return store.rooms()


@router.post("", response_model=Device, status_code=201, summary="Add a device")
def create_device(
    payload: DeviceCreate, store: DeviceStore = Depends(get_device_store)
) -> Device:
    return store.create(payload)


@router.get("/{device_id}", response_model=Device, summary="Get one device")
def get_device(device_id: str, store: DeviceStore = Depends(get_device_store)) -> Device:
    try:
        return store.get(device_id)
    except DeviceNotFound:
        raise HTTPException(status_code=404, detail="Device not found")


@router.patch("/{device_id}", response_model=Device, summary="Rename / move a device")
def update_device(
    device_id: str, payload: DeviceUpdate, store: DeviceStore = Depends(get_device_store)
) -> Device:
    try:
        return store.update_meta(device_id, payload)
    except DeviceNotFound:
        raise HTTPException(status_code=404, detail="Device not found")


@router.delete("/{device_id}", status_code=204, summary="Remove a device")
def delete_device(device_id: str, store: DeviceStore = Depends(get_device_store)) -> None:
    try:
        store.delete(device_id)
    except DeviceNotFound:
        raise HTTPException(status_code=404, detail="Device not found")


@router.post("/{device_id}/control", response_model=Device, summary="Control a device")
async def control_device(
    device_id: str, payload: ControlRequest, store: DeviceStore = Depends(get_device_store)
) -> Device:
    """Apply a partial state update, e.g. `{"state": {"is_on": true, "brightness": 60}}`.

    Fields are validated against the device type; unknown fields return 400.
    """
    try:
        return await store.control(device_id, payload.state)
    except DeviceNotFound:
        raise HTTPException(status_code=404, detail="Device not found")
    except DeviceUnreachable as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except InvalidControl as exc:
        raise HTTPException(status_code=400, detail=str(exc))
