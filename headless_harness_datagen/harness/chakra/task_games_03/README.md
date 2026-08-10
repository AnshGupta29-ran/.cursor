# Task 03: Endless Runner Game

This is a simple endless runner game implemented in Python using pygame.

## Features
- Player character that can jump to avoid obstacles
- Increasing difficulty over time
- Score tracking
- Restart functionality

## Controls
- SPACE: Jump
- R: Restart after game over

## How to Run
1. Install dependencies: `pip install -r requirements.txt`
2. Run the game: `python main.py`

## Game Mechanics
- The player runs continuously to the right
- Press SPACE to jump over obstacles
- Avoid hitting obstacles to survive longer
- The game speeds up gradually as you play
- Your score increases for each obstacle you pass

## Implementation Details
The game uses a simple physics system with gravity and jumping mechanics.
Obstacles are randomly generated with varying heights.
The difficulty increases over time by generating obstacles more frequently.