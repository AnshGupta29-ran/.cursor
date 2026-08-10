"""JSON persistence for Viper Trace: best scores and user settings."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

DATA_DIR = Path(__file__).resolve().parent / "data"
SCORES_FILE = DATA_DIR / "scores.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "difficulty": "hatchling",
    "speed": {},          # difficulty name -> last speed
    "show_explored": True,
}


def _load_json(path: Path, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp.replace(path)


def load_scores() -> Dict[str, int]:
    """Best scores keyed by "<difficulty>:<mode>"."""
    return _load_json(SCORES_FILE, {})


def get_best(difficulty: str, mode: str) -> int:
    return load_scores().get(f"{difficulty}:{mode}", 0)


def save_best(difficulty: str, mode: str, score: int) -> bool:
    """Persist score if it beats the record. Returns True if new best."""
    scores = load_scores()
    key = f"{difficulty}:{mode}"
    if score > scores.get(key, 0):
        scores[key] = score
        _save_json(SCORES_FILE, scores)
        return True
    return False


def load_settings() -> Dict[str, Any]:
    settings = dict(DEFAULT_SETTINGS)
    stored = _load_json(SETTINGS_FILE, {})
    if isinstance(stored, dict):
        settings.update(stored)
    return settings


def save_settings(settings: Dict[str, Any]) -> None:
    _save_json(SETTINGS_FILE, settings)
