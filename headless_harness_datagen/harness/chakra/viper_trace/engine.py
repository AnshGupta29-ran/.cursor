"""Core game engine for Viper Trace — pure logic, no rendering.

Runs identically with a Pygame front-end or headless in tests/smoke runs.
"""
from __future__ import annotations

import random
from collections import deque
from typing import Deque, List, Optional, Tuple

from .ai import AIStatus, TraceResult, next_direction, trace_decide
from .config import Difficulty
from .food import spawn_food
from .grid import Cell, Grid
from .snake import Snake

MODE_MANUAL = "manual"
MODE_AI = "ai"


class GameEngine:
    def __init__(
        self,
        difficulty: Difficulty,
        mode: str = MODE_MANUAL,
        seed: Optional[int] = None,
        speed: Optional[int] = None,
    ):
        self.difficulty = difficulty
        self.mode = mode
        self.grid = Grid(difficulty.width, difficulty.height, difficulty.obstacle_coords)
        seed_val = seed if seed is not None else random.randrange(1 << 30)
        self.rng = random.Random(f"{seed_val}:{difficulty.name}")
        center = (difficulty.width // 2, difficulty.height // 2)
        while self.grid.is_blocked(center):
            center = (center[0] + 1, center[1])
        self.snake = Snake([center, (center[0] - 1, center[1]), (center[0] - 2, center[1])])
        self.speed = (
            max(difficulty.min_speed, min(speed, difficulty.max_speed))
            if speed is not None
            else difficulty.start_speed
        )
        self.score = 0
        self.ticks = 0
        self.pellets = 0
        self.fallback_count = 0
        self.alive = True
        self.won = False
        self._queued_dirs: Deque[str] = deque(maxlen=3)
        self._applied_dir: str = self.snake.direction
        self.food: Optional[Cell] = None
        self._place_food()
        # AI overlay state
        self.ai_status: Optional[AIStatus] = None
        self.ai_path: List[Cell] = []
        self.ai_closed: set = set()

    # ------------------------------------------------------------------ input
    def queue_direction(self, direction: str) -> None:
        if not self.alive:
            return
        base = self._queued_dirs[-1] if self._queued_dirs else self._applied_dir
        opposites = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
        if opposites.get(direction) == base:
            return  # reject 180° reversal against latest pending direction
        self._queued_dirs.append(direction)

    def adjust_speed(self, delta: int) -> None:
        self.speed = max(
            self.difficulty.min_speed,
            min(self.speed + delta, self.difficulty.max_speed),
        )

    # ------------------------------------------------------------------- food
    def _place_food(self) -> None:
        try:
            self.food = spawn_food(self.grid, self.snake.body, self.rng)
        except RuntimeError:
            self.food = None
            self.won = True  # board full

    # ------------------------------------------------------------------- tick
    def tick(self) -> None:
        """Advance the game one fixed timestep."""
        if not self.alive or self.won:
            return
        self.ticks += 1
        if self.mode == MODE_AI and self.food is not None:
            result: TraceResult = trace_decide(self.grid, self.snake.body, self.food)
            self.ai_status = result.status
            self.ai_path = result.path
            self.ai_closed = result.closed_set
            if result.status is AIStatus.SAFE_ROUTE:
                direction = next_direction(self.snake.head, result.path[0])
            elif result.status is AIStatus.SURVIVAL_WANDER:
                self.fallback_count += 1
                direction = next_direction(self.snake.head, result.path[0])
            else:
                direction = None
            if direction:
                self.snake.set_direction(direction)
                self._applied_dir = direction
        else:
            if self._queued_dirs:
                direction = self._queued_dirs.popleft()
                self.snake.set_direction(direction)
                self._applied_dir = direction

        if not self.snake.move(self.grid):
            self.alive = False
            return

        if self.food is not None and self.snake.head == self.food:
            self.snake.grow()
            self.pellets += 1
            self.score += 1 * self.difficulty.score_multiplier
            self._place_food()
            if self.mode == MODE_AI and self.food is not None:
                result = trace_decide(self.grid, self.snake.body, self.food)
                self.ai_status = result.status
                self.ai_path = result.path
                self.ai_closed = result.closed_set

    # ------------------------------------------------------------------ stats
    @property
    def length(self) -> int:
        return len(self.snake.body)

    @property
    def hud_status(self) -> str:
        if self.mode != MODE_AI:
            return "TRACE: MANUAL"
        if self.ai_status is None:
            return "TRACE: --"
        return f"TRACE: {self.ai_status.value}"
