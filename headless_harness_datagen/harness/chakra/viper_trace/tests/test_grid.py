"""Tests for the Grid module."""
from viper_trace.grid import Grid
from viper_trace.config import HATCHLING, VIPER, APEX, DIFFICULTIES


def test_bounds_and_blocking():
    g = Grid(5, 5, obstacles=[(2, 2)])
    assert g.in_bounds((0, 0))
    assert g.in_bounds((4, 4))
    assert not g.in_bounds((-1, 0))
    assert not g.in_bounds((5, 0))
    assert g.is_blocked((2, 2))
    assert not g.is_blocked((1, 1))
    assert g.is_blocked((-1, 0))  # out of bounds counts as blocked


def test_neighbors_fixed_order():
    g = Grid(3, 3)
    assert g.neighbors((1, 1)) == [(1, 0), (2, 1), (1, 2), (0, 1)]  # N, E, S, W
    assert g.neighbors((0, 0)) == [(1, 0), (0, 1)]  # corner clipped


def test_add_remove_obstacle():
    g = Grid(4, 4)
    g.add_obstacle((1, 1))
    assert g.is_blocked((1, 1))
    g.remove_obstacle((1, 1))
    assert not g.is_blocked((1, 1))


def test_difficulty_presets_distinct():
    assert len(DIFFICULTIES) >= 3
    sizes = {(d.width, d.height) for d in (HATCHLING, VIPER, APEX)}
    assert len(sizes) == 3
    assert HATCHLING.start_speed < APEX.start_speed
    assert len(APEX.obstacle_coords) > len(HATCHLING.obstacle_coords)
    for d in (HATCHLING, VIPER, APEX):
        assert d.min_speed <= d.start_speed <= d.max_speed
        assert d.score_multiplier >= 1
        # all obstacles inside bounds
        for x, y in d.obstacle_coords:
            assert 0 <= x < d.width and 0 <= y < d.height
