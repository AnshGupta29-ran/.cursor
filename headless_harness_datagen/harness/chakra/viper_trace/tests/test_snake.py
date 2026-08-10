"""Tests for the Snake module."""
from viper_trace.grid import Grid
from viper_trace.snake import Snake


def make_snake():
    # head at (2,2), body extending left, facing RIGHT
    return Snake([(2, 2), (1, 2), (0, 2)], direction="RIGHT")


def test_move_advances_head_and_keeps_length():
    s = make_snake()
    g = Grid(10, 10)
    assert s.move(g)
    assert s.head == (3, 2)
    assert len(s.body) == 3
    assert (0, 2) not in s.body  # tail moved


def test_growth_adds_length():
    s = make_snake()
    g = Grid(10, 10)
    s.grow()
    s.move(g)
    assert len(s.body) == 4
    assert (0, 2) in s.body  # tail stayed


def test_wall_collision_kills():
    s = Snake([(0, 0), (0, 1), (0, 2)], direction="UP")
    g = Grid(10, 10)
    assert not s.move(g)  # would move to (0,-1)


def test_obstacle_collision_kills():
    s = make_snake()
    g = Grid(10, 10, obstacles=[(3, 2)])
    assert not s.move(g)


def test_self_collision_kills():
    # head at (1,1) moving DOWN into own neck cell (1,2)
    s = Snake([(1, 1), (1, 2), (2, 2), (2, 1)], direction="DOWN")
    g = Grid(10, 10)
    assert not s.move(g)


def test_tail_cell_is_safe_when_tail_moves():
    # classic rule: the tail cell is free because the tail vacates
    s = Snake([(1, 1), (2, 1), (2, 2), (1, 2)], direction="RIGHT")
    g = Grid(10, 10)
    # head at (1,1) moving RIGHT to (2,1) which is neck -> actually collision
    assert not s.move(g)
    # now a case where head moves into the tail's current cell:
    s2 = Snake([(2, 2), (2, 1), (1, 1), (1, 2)], direction="DOWN")
    # tail is (1,2); head (2,2) moving DOWN -> (2,3), free
    assert s2.move(g)
    s3 = Snake([(1, 2), (2, 2), (2, 1), (1, 1)], direction="UP")
    # head (1,2) UP -> (1,1) which is the tail: tail will vacate, safe
    assert s3.move(g)


def test_reject_180_reversal():
    s = make_snake()  # facing RIGHT
    s.set_direction("LEFT")
    assert s.direction == "RIGHT"  # rejected
    s.set_direction("UP")
    assert s.direction == "UP"
