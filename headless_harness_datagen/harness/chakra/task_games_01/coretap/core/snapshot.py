"""Snapshot codec: schema validation, RNG state encode/decode, file IO.

Schema v1 (see README "Snapshot format spec"):
  version, game, site_index, score, hulls, seed, rng_state, state,
  speed_bonus, rig_x, wide, timers, brick_bitmap, pulses, drops
"""
from __future__ import annotations

import json
import random
from typing import Any

from .constants import ALL_MODULES, BRICK_SPECS, SCHEMA_VERSION
from .persistence import atomic_write_json


class SnapshotError(Exception):
    """Clear, user-facing rejection of corrupt/tampered/unknown snapshots."""


# ----- RNG state -------------------------------------------------------------
def encode_rng(rng: random.Random) -> list:
    ver, state, gauss = rng.getstate()
    return [ver, list(state), gauss]


def decode_rng(payload: Any) -> random.Random:
    try:
        ver, state, gauss = payload
        rng = random.Random()
        rng.setstate((int(ver), tuple(int(x) for x in state), gauss))
        return rng
    except (TypeError, ValueError) as exc:
        raise SnapshotError(f"rng_state malformed: {exc}") from exc


# ----- validation -------------------------------------------------------------
def _num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_snapshot(snap: Any) -> None:
    if not isinstance(snap, dict):
        raise SnapshotError("snapshot is not a JSON object")
    if snap.get("version") != SCHEMA_VERSION:
        raise SnapshotError(
            f"unknown schema version {snap.get('version')!r} (expected {SCHEMA_VERSION})")
    if snap.get("game") != "coretap":
        raise SnapshotError("not a Core Tap snapshot")
    for f in ("site_index", "score", "hulls", "seed"):
        if not isinstance(snap.get(f), int):
            raise SnapshotError(f"field '{f}' must be int")
    if snap["hulls"] < 0 or snap["site_index"] < 0:
        raise SnapshotError("site_index/hulls must be >= 0")
    if snap.get("state") not in ("playing", "siteclear", "gameover", "win"):
        raise SnapshotError("field 'state' invalid")
    for f in ("speed_bonus", "rig_x"):
        if not _num(snap.get(f)):
            raise SnapshotError(f"field '{f}' must be number")
    if not isinstance(snap.get("wide"), bool):
        raise SnapshotError("field 'wide' must be bool")
    timers = snap.get("timers")
    if not isinstance(timers, dict):
        raise SnapshotError("field 'timers' must be object")
    for k, v in timers.items():
        if k not in ALL_MODULES or not _num(v) or v < 0:
            raise SnapshotError(f"timers entry {k!r} invalid")
    bm = snap.get("brick_bitmap")
    if not isinstance(bm, list):
        raise SnapshotError("field 'brick_bitmap' must be list")
    for cell in bm:
        if (not isinstance(cell, dict) or cell.get("cls") not in BRICK_SPECS
                or not isinstance(cell.get("hits"), int) or cell["hits"] < 0):
            raise SnapshotError("brick_bitmap cell invalid")
    pulses = snap.get("pulses")
    if not isinstance(pulses, list) or not pulses:
        raise SnapshotError("field 'pulses' must be non-empty list")
    for p in pulses:
        if not isinstance(p, dict):
            raise SnapshotError("pulse entry invalid")
        for f in ("x", "y", "vx", "vy"):
            if not _num(p.get(f)):
                raise SnapshotError(f"pulse field '{f}' must be number")
        if not isinstance(p.get("attached"), bool):
            raise SnapshotError("pulse field 'attached' must be bool")
    drops = snap.get("drops", [])
    if not isinstance(drops, list):
        raise SnapshotError("field 'drops' must be list")
    for d in drops:
        if (not isinstance(d, dict) or d.get("kind") not in ALL_MODULES
                or not _num(d.get("x")) or not _num(d.get("y"))):
            raise SnapshotError("drops entry invalid")
    decode_rng(snap.get("rng_state"))  # raises if malformed


# ----- file IO ----------------------------------------------------------------
def save_snapshot(path: str, snap: dict) -> None:
    atomic_write_json(path, snap)


def load_snapshot_file(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            snap = json.load(fh)
    except OSError as exc:
        raise SnapshotError(f"snapshot unreadable: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"snapshot is not valid JSON: {exc}") from exc
    validate_snapshot(snap)
    return snap
