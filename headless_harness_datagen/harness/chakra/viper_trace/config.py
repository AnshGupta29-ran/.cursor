"""Configuration for Viper Trace game.

Defines difficulty presets, obstacle layouts, and default settings.
"""
from dataclasses import dataclass
from typing import List, Tuple

@dataclass(frozen=True)
class Difficulty:
    name: str
    width: int
    height: int
    start_speed: int  # frames per second
    min_speed: int
    max_speed: int
    obstacle_coords: List[Tuple[int, int]]
    score_multiplier: int

# Helper to generate a rectangular border of obstacles (walls)
def border_obstacles(width: int, height: int) -> List[Tuple[int, int]]:
    obs = []
    for x in range(width):
        obs.append((x, 0))
        obs.append((x, height - 1))
    for y in range(1, height - 1):
        obs.append((0, y))
        obs.append((width - 1, y))
    return obs

# Preset difficulties
HATCHLING = Difficulty(
    name="Hatchling",
    width=20,
    height=20,
    start_speed=8,
    min_speed=4,
    max_speed=12,
    obstacle_coords=border_obstacles(20, 20),
    score_multiplier=1,
)

VIPER = Difficulty(
    name="Viper",
    width=30,
    height=25,
    start_speed=10,
    min_speed=6,
    max_speed=14,
    obstacle_coords=border_obstacles(30, 25) + [(10, y) for y in range(5, 20)],
    score_multiplier=2,
)

APEX = Difficulty(
    name="Apex",
    width=40,
    height=30,
    start_speed=12,
    min_speed=8,
    max_speed=16,
    obstacle_coords=border_obstacles(40, 30) + [
        (15, y) for y in range(10, 25)
    ] + [
        (25, y) for y in range(5, 20)
    ],
    score_multiplier=3,
)

DIFFICULTIES = {
    HATCHLING.name.lower(): HATCHLING,
    VIPER.name.lower(): VIPER,
    APEX.name.lower(): APEX,
}
