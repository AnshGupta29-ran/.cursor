# fov.py
"""Field of view computation using simple recursive shadowcasting.
Returns a set of (x, y) tuples that are visible from the origin within radius.
Walls ('#') block sight.
"""
from typing import Set, Tuple, List

def compute_fov(map_grid: List[List[str]], origin: Tuple[int, int], radius: int) -> Set[Tuple[int, int]]:
    ox, oy = origin
    visible: Set[Tuple[int, int]] = set()
    max_y = len(map_grid)
    max_x = len(map_grid[0]) if max_y else 0

    def blocks(x: int, y: int) -> bool:
        return map_grid[y][x] == '#'

    # Simple brute-force: iterate all tiles within radius and check line-of-sight using Bresenham
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            nx, ny = ox + dx, oy + dy
            if 0 <= nx < max_x and 0 <= ny < max_y:
                if dx * dx + dy * dy <= radius * radius:
                    if _los(ox, oy, nx, ny, blocks):
                        visible.add((nx, ny))
    return visible

def _los(x0: int, y0: int, x1: int, y1: int, blocker) -> bool:
    """Bresenham line-of-sight check. Returns True if no blocking tiles between (x0,y0) and (x1,y1)."""
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    n = 1 + dx + dy
    x_inc = 1 if x1 > x0 else -1
    y_inc = 1 if y1 > y0 else -1
    error = dx - dy
    dx *= 2
    dy *= 2
    for _ in range(n):
        if (x, y) != (x0, y0) and blocker(x, y):
            return False
        if x == x1 and y == y1:
            break
        if error > 0:
            x += x_inc
            error -= dy
        else:
            y += y_inc
            error += dx
    return True
