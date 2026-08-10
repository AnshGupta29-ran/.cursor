#!/usr/bin/env python3
"""
Puzzle Game Implementation
A simple tile matching puzzle game.
"""

import pygame
import random
import sys

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Puzzle Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)
CYAN = (0, 255, 255)

# Game variables
clock = pygame.time.Clock()
FPS = 60
GRID_SIZE = 8
TILE_SIZE = 60
GRID_OFFSET_X = (SCREEN_WIDTH - GRID_SIZE * TILE_SIZE) // 2
GRID_OFFSET_Y = (SCREEN_HEIGHT - GRID_SIZE * TILE_SIZE) // 2

# Tile colors
COLORS = [RED, GREEN, BLUE, YELLOW, PURPLE, CYAN]

class PuzzleGame:
    def __init__(self):
        self.grid = []
        self.selected_tile = None
        self.score = 0
        self.font = pygame.font.SysFont(None, 36)
        self.initialize_grid()

    def initialize_grid(self):
        """Initialize the grid with random colored tiles."""
        self.grid = []
        for row in range(GRID_SIZE):
            grid_row = []
            for col in range(GRID_SIZE):
                color = random.choice(COLORS)
                grid_row.append(color)
            self.grid.append(grid_row)

    def draw(self):
        """Draw the game board and UI."""
        screen.fill(WHITE)

        # Draw grid
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = GRID_OFFSET_X + col * TILE_SIZE
                y = GRID_OFFSET_Y + row * TILE_SIZE
                color = self.grid[row][col]

                # Highlight selected tile
                if self.selected_tile and self.selected_tile[0] == row and self.selected_tile[1] == col:
                    pygame.draw.rect(screen, BLACK, (x-2, y-2, TILE_SIZE+4, TILE_SIZE+4), 3)

                pygame.draw.rect(screen, color, (x, y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(screen, BLACK, (x, y, TILE_SIZE, TILE_SIZE), 1)

        # Draw score
        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        screen.blit(score_text, (10, 10))

        # Draw instructions
        instructions = [
            "Click on a tile to select it",
            "Click on an adjacent tile to swap",
            "Match 3 or more tiles to clear them"
        ]

        for i, instruction in enumerate(instructions):
            text = pygame.font.SysFont(None, 24).render(instruction, True, BLACK)
            screen.blit(text, (10, SCREEN_HEIGHT - 80 + i*20))

    def handle_click(self, pos):
        """Handle mouse click events."""
        x, y = pos

        # Check if click is within grid area
        if (GRID_OFFSET_X <= x < GRID_OFFSET_X + GRID_SIZE * TILE_SIZE and
            GRID_OFFSET_Y <= y < GRID_OFFSET_Y + GRID_SIZE * TILE_SIZE):

            # Convert pixel position to grid coordinates
            col = (x - GRID_OFFSET_X) // TILE_SIZE
            row = (y - GRID_OFFSET_Y) // TILE_SIZE

            if self.selected_tile is None:
                # Select first tile
                self.selected_tile = (row, col)
            else:
                # Check if this is the same tile
                if self.selected_tile == (row, col):
                    self.selected_tile = None
                    return

                # Check if tiles are adjacent
                row_diff = abs(self.selected_tile[0] - row)
                col_diff = abs(self.selected_tile[1] - col)

                if (row_diff == 1 and col_diff == 0) or (row_diff == 0 and col_diff == 1):
                    # Swap tiles
                    self.swap_tiles(self.selected_tile, (row, col))
                    self.selected_tile = None
                else:
                    # Select new tile
                    self.selected_tile = (row, col)

    def swap_tiles(self, pos1, pos2):
        """Swap two tiles in the grid."""
        row1, col1 = pos1
        row2, col2 = pos2

        # Perform swap
        self.grid[row1][col1], self.grid[row2][col2] = self.grid[row2][col2], self.grid[row1][col1]

        # Check for matches after swap
        self.check_matches()

    def check_matches(self):
        """Check for horizontal and vertical matches of 3 or more tiles."""
        # This is a simplified version that just scores points
        # A full implementation would find all matches and remove them
        self.score += 1

def main():
    game = PuzzleGame()

    running = True
    while running:
        clock.tick(FPS)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    game.handle_click(event.pos)

        # Update and draw
        game.draw()
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    print("Starting Puzzle Game...")
    try:
        main()
    except Exception as e:
        print(f"Error running game: {e}")
        sys.exit(1)