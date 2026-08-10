#!/usr/bin/env python3
"""
Endless Runner Game Implementation
This is a simple endless runner game where the player controls a character that runs continuously.
The goal is to avoid obstacles and survive as long as possible.
"""

import pygame
import random
import sys

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Endless Runner")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Game variables
clock = pygame.time.Clock()
FPS = 60
game_speed = 5
score = 0
font = pygame.font.SysFont(None, 36)

class Player:
    def __init__(self):
        self.width = 40
        self.height = 60
        self.x = 100
        self.y = SCREEN_HEIGHT - self.height - 50
        self.vel_y = 0
        self.jumping = False
        self.jump_power = -15
        self.gravity = 0.8

    def jump(self):
        if not self.jumping:
            self.vel_y = self.jump_power
            self.jumping = True

    def update(self):
        # Apply gravity
        self.vel_y += self.gravity
        self.y += self.vel_y

        # Ground collision
        if self.y >= SCREEN_HEIGHT - self.height - 50:
            self.y = SCREEN_HEIGHT - self.height - 50
            self.vel_y = 0
            self.jumping = False

    def draw(self):
        pygame.draw.rect(screen, BLUE, (self.x, self.y, self.width, self.height))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Obstacle:
    def __init__(self, x):
        self.width = 30
        self.height = random.randint(30, 70)
        self.x = x
        self.y = SCREEN_HEIGHT - self.height - 50
        self.speed = game_speed

    def update(self):
        self.x -= self.speed

    def draw(self):
        pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

def main():
    global game_speed, score

    player = Player()
    obstacles = []
    obstacle_timer = 0
    obstacle_frequency = 60  # frames between obstacles

    running = True
    game_over = False

    while running:
        clock.tick(FPS)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over:
                    player.jump()
                if event.key == pygame.K_r and game_over:
                    # Reset game
                    player = Player()
                    obstacles = []
                    game_speed = 5
                    score = 0
                    game_over = False

        if not game_over:
            # Update player
            player.update()

            # Generate obstacles
            obstacle_timer += 1
            if obstacle_timer >= obstacle_frequency:
                obstacles.append(Obstacle(SCREEN_WIDTH))
                obstacle_timer = 0
                # Gradually increase difficulty
                if obstacle_frequency > 30:
                    obstacle_frequency -= 0.1

            # Update obstacles
            for obstacle in obstacles[:]:
                obstacle.update()

                # Remove obstacles that are off screen
                if obstacle.x + obstacle.width < 0:
                    obstacles.remove(obstacle)
                    score += 1

                # Check collision
                if player.get_rect().colliderect(obstacle.get_rect()):
                    game_over = True

            # Increase speed over time
            game_speed += 0.001

        # Drawing
        screen.fill(WHITE)

        # Draw ground
        pygame.draw.rect(screen, GREEN, (0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50))

        # Draw player
        player.draw()

        # Draw obstacles
        for obstacle in obstacles:
            obstacle.draw()

        # Draw score
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))

        # Draw game over message
        if game_over:
            game_over_text = font.render("Game Over! Press R to restart", True, BLACK)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(game_over_text, text_rect)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    print("Starting Endless Runner Game...")
    try:
        main()
    except Exception as e:
        print(f"Error running game: {e}")
        sys.exit(1)