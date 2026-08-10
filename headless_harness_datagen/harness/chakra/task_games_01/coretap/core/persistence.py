"""JSON persistence: atomic writes, schema-validated reads.

Highscores and settings regenerate silently when missing or corrupt.
"""
from __future__ import annotations

import json
import os
from typing import Any

SCHEMA_VERSION = 1


def atomic_write_json(path: str, payload: Any) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_highscores(path: str) -> list[dict]:
    """Top-10 list of {callsign, score, site}. Corrupt/missing -> empty list."""
    try:
        data = _read_json(path)
        if (isinstance(data, dict) and data.get("version") == SCHEMA_VERSION
                and isinstance(data.get("scores"), list)):
            out = []
            for e in data["scores"]:
                if (isinstance(e, dict) and isinstance(e.get("callsign"), str)
                        and isinstance(e.get("score"), int)):
                    out.append({"callsign": e["callsign"][:3].upper(),
                                "score": e["score"],
                                "site": str(e.get("site", "?"))})
            return sorted(out, key=lambda e: -e["score"])[:10]
    except (OSError, json.JSONDecodeError, ValueError):
        pass
    return []


def save_highscores(path: str, scores: list[dict]) -> None:
    scores = sorted(scores, key=lambda e: -e["score"])[:10]
    atomic_write_json(path, {"version": SCHEMA_VERSION, "game": "coretap",
                             "scores": scores})


DEFAULT_SETTINGS = {"difficulty": "standard", "mute": False, "game_speed": 1.0}


def load_settings(path: str) -> dict:
    try:
        data = _read_json(path)
        if isinstance(data, dict) and data.get("version") == SCHEMA_VERSION:
            out = dict(DEFAULT_SETTINGS)
            s = data.get("settings", {})
            if isinstance(s, dict):
                if s.get("difficulty") in ("standard", "hard"):
                    out["difficulty"] = s["difficulty"]
                out["mute"] = bool(s.get("mute", False))
                gs = s.get("game_speed", 1.0)
                if isinstance(gs, (int, float)) and 0.5 <= gs <= 2.0:
                    out["game_speed"] = float(gs)
            return out
    except (OSError, json.JSONDecodeError, ValueError):
        pass
    return dict(DEFAULT_SETTINGS)


def save_settings(path: str, settings: dict) -> None:
    atomic_write_json(path, {"version": SCHEMA_VERSION, "settings": settings})
