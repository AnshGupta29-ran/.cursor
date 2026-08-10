"""Historical sensor readings."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import get_device_store, get_reading_store
from ..models import Reading
from ..readings_store import ReadingStore
from ..store import DeviceNotFound, DeviceStore

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/{device_id}", response_model=list[Reading], summary="Sensor history for a device")
def device_history(
    device_id: str,
    start: Optional[float] = Query(default=None, description="Unix timestamp, inclusive"),
    end: Optional[float] = Query(default=None, description="Unix timestamp, inclusive"),
    limit: int = Query(default=500, ge=1, le=5000),
    readings: ReadingStore = Depends(get_reading_store),
    devices: DeviceStore = Depends(get_device_store),
) -> list[Reading]:
    """Readings are returned oldest-first. Which fields are populated depends on
    the device type: thermostats record temperature/humidity/power, cameras
    record motion, lights and fans record power."""
    try:
        devices.get(device_id)
    except DeviceNotFound:
        raise HTTPException(status_code=404, detail="Device not found")
    return readings.query(device_id, start=start, end=end, limit=limit)
