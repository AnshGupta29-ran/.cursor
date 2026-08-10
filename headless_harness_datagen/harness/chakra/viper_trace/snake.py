"""Snake implementation for Viper Trace.

Manages the list of body cells, direction, movement, growth, and collision detection.
"""
from typing import List, Tuple
from .grid import Grid, Cell

# Direction vectors
DIR_VECTORS = {
    "UP": (0, -1),
    "DOWN": (0, 1),
    "LEFT": (-1, 0),
    "RIGHT": (1, 0),
}

OPPOSITE = {
    "UP": "DOWN",
    "DOWN": "UP",
    "LEFT": "RIGHT",
    "RIGHT": "LEFT",
}

class Snake:
    def __init__(self, init_cells: List[Cell], direction: str = "RIGHT"):
        if direction not in DIR_VECTORS:
            raise ValueError("Invalid initial direction")
        self.body: List[Cell] = list(init_cells)  # head is first element
        self.direction = direction
        self.grow_pending = 0

    @property
    def head(self) -> Cell:
        return self.body[0]

    def set_direction(self, new_dir: str) -> None:
        """Queue a new direction if not opposite to current direction.
        Caller should handle input rate limiting; this method just validates.
        """
        if new_dir not in DIR_VECTORS:
            return
        if OPPOSITE[new_dir] == self.direction:
            # Reject 180° turn
            return
        self.direction = new_dir

    def move(self, grid: Grid) -> bool:
        """Advance the snake one step.
        Returns True if move is successful, False if collision occurs.
        """
        dx, dy = DIR_VECTORS[self.direction]
        new_head = (self.head[0] + dx, self.head[1] + dy)
        # Collision with walls/obstacles
        if grid.is_blocked(new_head):
            return False
        # Collision with self (excluding tail if it will move away)
        if new_head in self.body[:-1]:
            return False
        # Insert new head
        self.body.insert(0, new_head)
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            # Remove tail
            self.body.pop()
        return True

    def grow(self, amount: int = 1) -> None:
        self.grow_pending += amount

    def occupies(self, cell: Cell) -> bool:
        return cell in self.body
