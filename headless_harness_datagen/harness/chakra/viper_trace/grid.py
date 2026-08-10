"""Grid implementation for Viper Trace.

Provides cell occupancy checks, neighbor lookup, and obstacle handling.
"""
from typing import List, Tuple, Set

Cell = Tuple[int, int]  # (x, y) coordinate

class Grid:
    def __init__(self, width: int, height: int, obstacles: List[Cell] = None):
        self.width = width
        self.height = height
        self._obstacle_set: Set[Cell] = set(obstacles or [])

    def in_bounds(self, cell: Cell) -> bool:
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height

    def is_blocked(self, cell: Cell) -> bool:
        """Return True if cell is a wall, obstacle, or outside bounds."""
        if not self.in_bounds(cell):
            return True
        return cell in self._obstacle_set

    def neighbors(self, cell: Cell) -> List[Cell]:
        """Return orthogonal neighboring cells (N, E, S, W) that are within bounds.
        Does NOT filter obstacles; callers should check is_blocked as needed.
        """
        x, y = cell
        candidates = [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]
        return [c for c in candidates if self.in_bounds(c)]

    def add_obstacle(self, cell: Cell) -> None:
        if self.in_bounds(cell):
            self._obstacle_set.add(cell)

    def remove_obstacle(self, cell: Cell) -> None:
        self._obstacle_set.discard(cell)

    def obstacle_cells(self) -> Set[Cell]:
        return set(self._obstacle_set)
