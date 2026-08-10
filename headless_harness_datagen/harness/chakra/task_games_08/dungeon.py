# dungeon.py
"""Procedural dungeon generation for Deepvault Survey.
Simplified version: rectangular rooms with corridors, seeded deterministic.
"""
import random
from typing import List, Tuple, Set

class Dungeon:
    def __init__(self, width: int, height: int, prng_func):
        self.width = width
        self.height = height
        self.prng_func = prng_func
        self.map: List[List[str]] = [["#" for _ in range(width)] for _ in range(height)]
        self.remembered: Set[Tuple[int, int]] = set()
        self.current_floor = 1
        self.start_pos: Tuple[int, int] = (1, 1)
        self._generate()

    def _randint(self, a, b):
        # use supplied prng_func to get deterministic float 0-1
        return a + int(self.prng_func() * (b - a + 1))

    def _generate(self):
        # carve out a simple open area for demo purposes
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                self.map[y][x] = "."
        # place start
        sx, sy = self.start_pos
        self.map[sy][sx] = "@"
        # place shaft and heart on farthest positions (simplified)
        self.map[self.height - 2][self.width - 2] = ">"
        self.map[self.height - 3][self.width - 3] = "&"

    def random_free_position(self, prng_func) -> Tuple[int, int]:
        while True:
            x = self._randint(1, self.width - 2)
            y = self._randint(1, self.height - 2)
            if self.map[y][x] == ".":
                return (x, y)
