"""Trace Engine: survival-aware A* search for Viper Trace.

Pure-Python, headless-testable logic. No rendering code here.

Pipeline per decision tick:
1. A* from snake head to food over free cells (walls, obstacles, snake body
   blocked). Manhattan heuristic, 4-neighborhood, deterministic tie-breaking.
2. Survival gate: simulate eating along the candidate path; commit only if the
   post-meal head can still reach its own tail (BFS reachability).
3. Fallback ("survival wander"): when no safe route exists, choose the legal
   move maximizing flood-fill reachable free area. Never picks a suicide move
   while a survivable one exists.
"""
from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence, Set, Tuple

from ..grid import Grid, Cell
from ..snake import DIR_VECTORS


class AIStatus(Enum):
    SAFE_ROUTE = "SAFE ROUTE"
    SURVIVAL_WANDER = "SURVIVAL WANDER"
    NO_PATH = "NO PATH"


@dataclass
class TraceResult:
    status: AIStatus
    path: List[Cell]  # committed path head->food (SAFE_ROUTE) or fallback step
    closed_set: Set[Cell] = field(default_factory=set)


def manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def a_star(
    grid: Grid,
    start: Cell,
    goal: Cell,
    extra_blocked: Set[Cell] = frozenset(),
) -> Tuple[Optional[List[Cell]], Set[Cell]]:
    """A* shortest path, 4-neighborhood, Manhattan heuristic.

    Cells are blocked if the grid says so or if they are in ``extra_blocked``
    (e.g. the snake's body). Ties broken deterministically by insertion order;
    neighbors are expanded in a fixed N, E, S, W order.

    Returns ``(path, closed_set)`` where ``path`` excludes ``start`` and ends at
    ``goal``, or ``(None, closed_set)`` if no route exists.
    """
    def blocked(c: Cell) -> bool:
        return grid.is_blocked(c) or c in extra_blocked

    if blocked(goal):
        return None, set()

    # neighbor offsets in fixed order: N, E, S, W
    neighbor_offsets = [(0, -1), (1, 0), (0, 1), (-1, 0)]

    open_heap: List[Tuple[int, int, Cell]] = []
    counter = 0
    g_score: Dict[Cell, int] = {start: 0}
    came_from: Dict[Cell, Cell] = {}
    heapq.heappush(open_heap, (manhattan(start, goal), counter, start))
    closed: Set[Cell] = set()

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current == goal:
            path: List[Cell] = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path[1:], closed  # exclude start
        if current in closed:
            continue
        closed.add(current)
        for dx, dy in neighbor_offsets:
            neighbor = (current[0] + dx, current[1] + dy)
            if not grid.in_bounds(neighbor) or blocked(neighbor) or neighbor in closed:
                continue
            tentative = g_score[current] + 1
            if tentative < g_score.get(neighbor, 1 << 30):
                g_score[neighbor] = tentative
                came_from[neighbor] = current
                counter += 1
                f = tentative + manhattan(neighbor, goal)
                heapq.heappush(open_heap, (f, counter, neighbor))
    return None, closed


def simulate_meal(
    body: Sequence[Cell], path: Sequence[Cell]
) -> List[Cell]:
    """Simulate the snake moving along ``path`` and eating at its end.

    ``body`` is head-first. The snake advances one cell per path step; the tail
    stays put on the final step (growth). Returns the new head-first body.
    """
    new_body = list(body)
    for i, cell in enumerate(path):
        new_body.insert(0, cell)
        if i < len(path) - 1:
            new_body.pop()
    return new_body


def bfs_reachable(
    grid: Grid,
    start: Cell,
    goal: Cell,
    blocked_cells: Set[Cell],
) -> bool:
    """True if ``goal`` is reachable from ``start`` avoiding blocked cells."""
    if start == goal:
        return True
    visited: Set[Cell] = {start}
    queue: deque[Cell] = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in grid.neighbors(current):
            if neighbor == goal:
                return True
            if (
                neighbor in visited
                or neighbor in blocked_cells
                or grid.is_blocked(neighbor)
            ):
                continue
            visited.add(neighbor)
            queue.append(neighbor)
    return False


def survival_gate(
    grid: Grid,
    path: Sequence[Cell],
    body: Sequence[Cell],
) -> bool:
    """True if committing to ``path`` leaves the snake survivable.

    Simulates the meal; the post-meal head must be able to reach the tail cell.
    If the meal fills the board (single free cell), the run is a win — safe.
    """
    if not path:
        return False
    post_body = simulate_meal(body, path)
    post_head = post_body[0]
    blocked: Set[Cell] = set(post_body[1:])
    if len(post_body) >= grid.width * grid.height - len(grid.obstacle_cells()):
        return True  # board full: win state
    return bfs_reachable(grid, post_head, post_body[-1], blocked)


def flood_fill_area(
    grid: Grid,
    start: Cell,
    blocked_cells: Set[Cell],
) -> int:
    """Count of free cells reachable from ``start`` (0 if start is blocked)."""
    if grid.is_blocked(start) or start in blocked_cells:
        return 0
    visited: Set[Cell] = {start}
    queue: deque[Cell] = deque([start])
    count = 0
    while queue:
        current = queue.popleft()
        count += 1
        for neighbor in grid.neighbors(current):
            if (
                neighbor in visited
                or neighbor in blocked_cells
                or grid.is_blocked(neighbor)
            ):
                continue
            visited.add(neighbor)
            queue.append(neighbor)
    return count


def fallback_move(grid: Grid, body: Sequence[Cell]) -> Tuple[Optional[Cell], Set[Cell]]:
    """Survival wander: pick the legal move maximizing reachable free area.

    Returns ``(next_cell, closed_set)``; ``next_cell`` is None when every
    neighbor of the head is lethal (unavoidable death). A move that lets the
    snake still reach its own tail always outranks one that doesn't, so the
    fallback never suicides while a survivable option exists.
    """
    head = body[0]
    tail = body[-1]
    body_set = set(body)
    candidates: List[Tuple[int, int, int, Cell]] = []  # (safe, area, order, cell)
    closed: Set[Cell] = set()
    for order, (name, (dx, dy)) in enumerate(DIR_VECTORS.items()):
        neighbor = (head[0] + dx, head[1] + dy)
        if grid.is_blocked(neighbor) or (neighbor in body_set and neighbor != tail):
            continue  # lethal
        new_body = [neighbor] + list(body[:-1])
        new_blocked = set(new_body[1:])
        if new_body[0] == new_body[-1]:
            safe = 1
        else:
            safe = 1 if bfs_reachable(grid, new_body[0], new_body[-1], new_blocked) else 0
        area = flood_fill_area(grid, neighbor, new_blocked)
        candidates.append((safe, area, order, neighbor))
    if not candidates:
        return None, closed
    # safe first, then max area, then fixed direction order for determinism
    candidates.sort(key=lambda t: (-t[0], -t[1], t[2]))
    return candidates[0][3], closed


def trace_decide(
    grid: Grid,
    body: Sequence[Cell],
    food: Cell,
) -> TraceResult:
    """Decide the snake's next route.

    SAFE_ROUTE: A* path to food passed the survival gate.
    SURVIVAL_WANDER: no safe route; flood-fill fallback chosen.
    NO_PATH: no legal move at all (death unavoidable).
    """
    head = body[0]
    tail = body[-1]
    body_set = set(body)
    blocked = body_set - {tail}  # tail vacates as we move
    path, closed = a_star(grid, head, food, blocked)
    if path is not None and survival_gate(grid, path, body):
        return TraceResult(AIStatus.SAFE_ROUTE, path, closed)
    fallback, _ = fallback_move(grid, body)
    if fallback is not None:
        return TraceResult(AIStatus.SURVIVAL_WANDER, [fallback], closed)
    return TraceResult(AIStatus.NO_PATH, [], closed)


def next_direction(head: Cell, next_cell: Cell) -> Optional[str]:
    """Direction name from ``head`` to adjacent ``next_cell``."""
    dx = next_cell[0] - head[0]
    dy = next_cell[1] - head[1]
    for name, (vx, vy) in DIR_VECTORS.items():
        if (vx, vy) == (dx, dy):
            return name
    return None
