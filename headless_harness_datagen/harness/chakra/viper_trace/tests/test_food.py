"""Tests for deterministic food spawning."""
import random

import pytest

from viper_trace.food import spawn_food
from viper_trace.grid import Grid


def test_food_never_on_occupied_cells():
    g = Grid(6, 6, obstacles=[(0, 0)])
    body = [(1, 1), (2, 1), (3, 1)]
    rng = random.Random(123)
    for _ in range(50):
        cell = spawn_food(g, body, rng)
        assert cell not in body
        assert not g.is_blocked(cell)


def test_seed_reproduces_sequence():
    g = Grid(8, 8)
    body = [(0, 0)]
    rng_b = random.Random(42)
    seq_b = [spawn_food(g, body, rng_b) for _ in range(5)]
    rng_c = random.Random(42)
    seq_c = [spawn_food(g, body, rng_c) for _ in range(5)]
    assert seq_b == seq_c


def test_full_board_raises():
    g = Grid(2, 1)  # only two cells
    body = [(0, 0), (1, 0)]
    with pytest.raises(RuntimeError):
        spawn_food(g, body, random.Random(1))
