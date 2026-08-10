"""Headless engine tests: input buffering, AI smoke run, determinism, persistence."""
import json

from viper_trace import persistence
from viper_trace.config import APEX, HATCHLING, VIPER
from viper_trace.engine import GameEngine, MODE_AI, MODE_MANUAL


def test_input_buffer_rejects_reverse_and_spam_death():
    eng = GameEngine(HATCHLING, MODE_MANUAL, seed=1)
    # facing RIGHT; quick LEFT then UP must not reverse
    eng.queue_direction("LEFT")
    eng.queue_direction("UP")
    eng.tick()
    assert eng.snake.direction == "UP"
    assert eng.alive


def test_manual_wall_death():
    eng = GameEngine(HATCHLING, MODE_MANUAL, seed=1)
    for _ in range(HATCHLING.width):
        eng.tick()
    assert not eng.alive  # ran straight into the right border wall


def test_speed_bounds():
    eng = GameEngine(HATCHLING, MODE_MANUAL, seed=1)
    for _ in range(50):
        eng.adjust_speed(1)
    assert eng.speed == HATCHLING.max_speed
    for _ in range(50):
        eng.adjust_speed(-1)
    assert eng.speed == HATCHLING.min_speed


def test_seed_reproduces_food_sequence():
    e1 = GameEngine(HATCHLING, MODE_AI, seed=7)
    e2 = GameEngine(HATCHLING, MODE_AI, seed=7)
    for _ in range(300):
        if e1.alive and not e1.won:
            e1.tick()
        if e2.alive and not e2.won:
            e2.tick()
    assert e1.food == e2.food
    assert e1.score == e2.score
    assert e1.snake.body == e2.snake.body


def test_ai_smoke_run_scores_and_survives():
    # smoke: fixed-seed headless AI run must score within a bounded tick count
    for difficulty in (HATCHLING, VIPER, APEX):
        eng = GameEngine(difficulty, MODE_AI, seed=42)
        for _ in range(3000):
            if eng.score > 0 or not eng.alive or eng.won:
                break
            eng.tick()
        assert eng.score > 0, f"{difficulty.name}: AI scored 0 within 3000 ticks"
        assert eng.pellets > 0


def test_ai_survives_long_open_run():
    # on the open Hatchling grid the trace engine should last a long time
    eng = GameEngine(HATCHLING, MODE_AI, seed=99)
    for _ in range(3000):
        if not eng.alive or eng.won:
            break
        eng.tick()
    assert eng.alive or eng.won
    assert eng.pellets >= 5


def test_persistence_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(persistence, "DATA_DIR", tmp_path)
    monkeypatch.setattr(persistence, "SCORES_FILE", tmp_path / "scores.json")
    monkeypatch.setattr(persistence, "SETTINGS_FILE", tmp_path / "settings.json")

    assert persistence.get_best("Viper", MODE_AI) == 0
    assert persistence.save_best("Viper", MODE_AI, 12) is True
    assert persistence.save_best("Viper", MODE_AI, 5) is False  # not a record
    assert persistence.get_best("Viper", MODE_AI) == 12
    # file on disk is valid JSON
    data = json.loads((tmp_path / "scores.json").read_text())
    assert data["Viper:ai"] == 12

    settings = persistence.load_settings()
    settings["difficulty"] = "apex"
    settings["show_explored"] = False
    persistence.save_settings(settings)
    loaded = persistence.load_settings()
    assert loaded["difficulty"] == "apex"
    assert loaded["show_explored"] is False
