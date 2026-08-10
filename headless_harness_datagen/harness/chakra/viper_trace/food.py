"""Food handling for Viper Trace.

Provides deterministic food placement using a seeded random generator.
"""
import random
from typing import List, Tuple
from .grid import Grid, Cell

def spawn_food(grid: Grid, snake_body: List[Cell], rng: random.Random) -> Cell:
    """Return a free cell for food.
    Ensures the cell is not occupied by the snake or obstacles.
    """
    free_cells = [
        (x, y)
        for x in range(grid.width)
        for y in range(grid.height)
        if not grid.is_blocked((x, y)) and (x, y) not in snake_body
    ]
    if not free_cells:
        raise RuntimeError("No free cells available for food")
    return rng.choice(free_cells)
