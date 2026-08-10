"""Proves a real AI run exercises the survival-wander fallback, not just A*."""
from viper_trace.ai import AIStatus
from viper_trace.config import VIPER
from viper_trace.engine import GameEngine, MODE_AI


def test_long_run_exercises_fallback():
    eng = GameEngine(VIPER, MODE_AI, seed=0)
    wander_ticks = 0
    for _ in range(6000):
        if not eng.alive or eng.won:
            break
        eng.tick()
        if eng.ai_status is AIStatus.SURVIVAL_WANDER:
            wander_ticks += 1
    assert eng.fallback_count > 0
    assert wander_ticks > 0
    assert eng.pellets > 0  # kept eating while surviving
