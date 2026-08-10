"""Automation rules: WHEN a sensor crosses a threshold, THEN control a device."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_device_store, get_rule_store
from ..models import CameraState, Rule, RuleCreate, RuleUpdate, ThermostatState
from ..store import DeviceNotFound, DeviceStore, RuleStore

router = APIRouter(prefix="/api/rules", tags=["rules"])

_SENSOR_STATE = {
    "temperature": ThermostatState,
    "humidity": ThermostatState,
    "motion": CameraState,
}


def _validate_rule(payload: RuleCreate, devices: DeviceStore) -> None:
    try:
        source = devices.get(payload.source_device_id)
        devices.get(payload.target_device_id)
    except DeviceNotFound:
        raise HTTPException(status_code=404, detail="Source or target device not found")
    expected = _SENSOR_STATE[payload.metric]
    if not isinstance(source.state, expected):
        raise HTTPException(
            status_code=400,
            detail=f"Metric '{payload.metric}' is not available on a {source.type.value}",
        )


@router.get("", response_model=list[Rule], summary="List rules")
def list_rules(store: RuleStore = Depends(get_rule_store)) -> list[Rule]:
    return store.list()


@router.post("", response_model=Rule, status_code=201, summary="Create a rule")
def create_rule(
    payload: RuleCreate,
    store: RuleStore = Depends(get_rule_store),
    devices: DeviceStore = Depends(get_device_store),
) -> Rule:
    _validate_rule(payload, devices)
    return store.create(payload)


@router.patch("/{rule_id}", response_model=Rule, summary="Update a rule")
def update_rule(
    rule_id: str, payload: RuleUpdate, store: RuleStore = Depends(get_rule_store)
) -> Rule:
    try:
        return store.update(rule_id, payload)
    except DeviceNotFound:
        raise HTTPException(status_code=404, detail="Rule not found")


@router.delete("/{rule_id}", status_code=204, summary="Delete a rule")
def delete_rule(rule_id: str, store: RuleStore = Depends(get_rule_store)) -> None:
    try:
        store.delete(rule_id)
    except DeviceNotFound:
        raise HTTPException(status_code=404, detail="Rule not found")
