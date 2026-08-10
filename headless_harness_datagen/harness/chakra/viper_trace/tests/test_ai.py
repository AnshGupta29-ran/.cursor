"""Tests for the Trace Engine: A*, survival gate, flood-fill fallback."""
from viper_trace.ai import (
    AIStatus,
    a_star,
    bfs_reachable,
    fallback_move,
    flood_fill_area,
    simulate_meal,
    survival_gate,
    trace_decide,
)
from viper_trace.grid import Grid


# ---------------------------------------------------------------- A* basics
def test_astar_open_grid_shortest():
    g = Grid(10, 10)
    path, closed = a_star(g, (0, 0), (5, 3))
    assert path is not None
    assert len(path) == 8  # manhattan distance
    assert path[-1] == (5, 3)
    assert (0, 0) not in path  # start excluded
    assert closed  # explored set non-empty
    # path must be a valid walk
    prev = (0, 0)
    for cell in path:
        assert abs(cell[0] - prev[0]) + abs(cell[1] - prev[1]) == 1
        prev = cell


def test_astar_detours_around_obstacle():
    # vertical wall at x=2 with a gap at y=4
    wall = [(2, y) for y in range(5) if y != 4]
    g = Grid(6, 5, obstacles=wall)
    path, _ = a_star(g, (0, 0), (4, 0))
    assert path is not None
    assert (2, 4) in path  # must route through the gap
    assert all(c not in wall for c in path)


def test_astar_returns_none_when_sealed():
    # goal completely enclosed by obstacles
    sealed = [(1, 1), (3, 1), (2, 0), (1, 2), (3, 2), (1, 3), (2, 3), (3, 3)]
    g = Grid(5, 5, obstacles=sealed)
    path, _ = a_star(g, (0, 0), (2, 2))
    assert path is None


def test_astar_respects_body_blocked():
    g = Grid(6, 6)
    body = {(2, 0), (2, 1), (2, 2), (2, 3), (2, 4)}
    path, _ = a_star(g, (0, 0), (4, 0), extra_blocked=body)
    assert path is not None
    assert all(c not in body for c in path)
    assert (2, 5) in path  # only gap is below the body wall


def test_astar_deterministic():
    g = Grid(10, 10)
    p1, _ = a_star(g, (0, 0), (7, 6))
    p2, _ = a_star(g, (0, 0), (7, 6))
    assert p1 == p2


# ------------------------------------------------------------ survival gate
def test_survival_gate_accepts_safe_path():
    g = Grid(10, 10)
    body = [(2, 2), (1, 2), (0, 2)]
    path, _ = a_star(g, (2, 2), (8, 2))
    assert survival_gate(g, path, body)


def test_survival_gate_rejects_trap():
    # 3x3 grid, walls left and right of the middle row; head at (1,1),
    # body stretches down. Stepping up to (1,0) is a cul-de-sac: after the
    # meal the head is boxed in by its own body and cannot reach the tail.
    g = Grid(3, 3, obstacles=[(0, 0), (2, 0)])
    body = [(1, 1), (1, 2), (0, 2)]
    assert not survival_gate(g, [(1, 0)], body)


def test_simulate_meal_grows_once():
    body = [(2, 2), (1, 2), (0, 2)]
    post = simulate_meal(body, [(3, 2), (4, 2)])
    assert post == [(4, 2), (3, 2), (2, 2), (1, 2)]
    assert len(post) == len(body) + 1


# ------------------------------------------------------------- flood/fallback
def test_flood_fill_area_counts_free_region():
    g = Grid(5, 5, obstacles=[(2, y) for y in range(5)])
    assert flood_fill_area(g, (0, 0), set()) == 10  # left half
    assert flood_fill_area(g, (2, 2), set()) == 0   # on a wall


def test_fallback_refuses_suicide_when_alternative_exists():
    # head at (1,0): UP/LEFT are walls (out of bounds counts), RIGHT is neck,
    # only DOWN survives -> fallback must pick DOWN, not a lethal cell
    g = Grid(4, 4)
    body = [(1, 0), (2, 0), (3, 0), (3, 1)]
    cell, _ = fallback_move(g, body)
    assert cell == (1, 1)

    # trap: head in a cul-de-sac, one exit leads to open space, the other
    # to a sealed pocket. Fallback must prefer the survivable exit.
    #   row 0: H . #
    #   row 1: S S .
    #   row 2: . . .
    obstacles = [(2, 0)]
    g = Grid(3, 3, obstacles=obstacles)
    body = [(0, 0), (0, 1), (1, 1)]  # head at top-left, facing pocket vs open
    cell, _ = fallback_move(g, body)
    # options from (0,0): RIGHT (1,0) open area; DOWN is neck (lethal).
    assert cell == (1, 0)
    assert cell not in body[:1]


def test_fallback_none_when_surrounded():
    g = Grid(3, 3)
    body = [(1, 1), (1, 0), (0, 1), (2, 1), (1, 2)]
    # head fully boxed by its own body (tail (1,2) will move, so only DOWN ok)
    cell, _ = fallback_move(g, body)
    assert cell == (1, 2)  # tail cell is legal (tail vacates)
    # now block the tail too via an obstacle: no legal moves remain
    g2 = Grid(3, 3, obstacles=[(1, 2)])
    cell2, _ = fallback_move(g2, body)
    assert cell2 is None


def test_bfs_reachable():
    g = Grid(5, 5, obstacles=[(2, y) for y in range(4)])
    assert bfs_reachable(g, (0, 0), (4, 4), set())   # around the wall bottom
    assert not bfs_reachable(g, (0, 0), (4, 4), {(3, 4), (4, 3)})  # sealed goal


# ------------------------------------------------------------- trace_decide
def test_trace_decide_safe_route_on_open_grid():
    g = Grid(10, 10)
    body = [(2, 2), (1, 2), (0, 2)]
    result = trace_decide(g, body, (8, 8))
    assert result.status is AIStatus.SAFE_ROUTE
    assert result.path[-1] == (8, 8)
    assert result.closed_set


def test_trace_decide_fallback_when_food_unreachable():
    sealed = [(1, 1), (3, 1), (2, 0), (1, 2), (3, 2), (1, 3), (2, 3), (3, 3)]
    g = Grid(5, 5, obstacles=sealed)
    body = [(0, 0), (0, 1), (0, 2)]
    result = trace_decide(g, body, (2, 2))  # sealed food
    assert result.status is AIStatus.SURVIVAL_WANDER
    assert len(result.path) == 1  # single fallback step
    assert result.path[0] not in body[:-1] or result.path[0] == body[-1]


def test_trace_decide_no_path_when_doomed():
    g = Grid(3, 3, obstacles=[(1, 2)])
    body = [(1, 1), (1, 0), (0, 1), (2, 1), (1, 2)]
    result = trace_decide(g, body, (0, 0))
    assert result.status is AIStatus.NO_PATH
    assert result.path == []
