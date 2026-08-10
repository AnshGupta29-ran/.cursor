#!/usr/bin/env python3
"""
Adventure Game Implementation
A simple text-based adventure game with exploration and narrative elements.
"""

import pygame
import sys

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Adventure Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)

# Game variables
clock = pygame.time.Clock()
FPS = 60
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)

class Player:
    def __init__(self):
        self.name = "Hero"
        self.health = 100
        self.inventory = []
        self.location = "forest"

class AdventureGame:
    def __init__(self):
        self.player = Player()
        self.game_state = "playing"  # playing, game_over, victory
        self.current_scene = "forest_start"
        self.scenes = {
            "forest_start": {
                "description": "You find yourself in a dark forest. Paths lead north, east, and west.",
                "choices": [
                    {"text": "Go North", "next_scene": "cave"},
                    {"text": "Go East", "next_scene": "village"},
                    {"text": "Go West", "next_scene": "river"}
                ],
                "items": ["torch"]
            },
            "cave": {
                "description": "You enter a mysterious cave. It's very dark inside. You can see something shiny near the back.",
                "choices": [
                    {"text": "Investigate the shiny object", "next_scene": "treasure_room"},
                    {"text": "Return to forest", "next_scene": "forest_start"}
                ],
                "items": []
            },
            "village": {
                "description": "You arrive at a small village. The villagers seem friendly. There's a market where you can buy supplies.",
                "choices": [
                    {"text": "Visit the market", "next_scene": "market"},
                    {"text": "Talk to the villagers", "next_scene": "village_talk"},
                    {"text": "Return to forest", "next_scene": "forest_start"}
                ],
                "items": ["bread", "health_potion"]
            },
            "river": {
                "description": "You reach a river. The water looks clear and fresh. You could drink from it or build a raft.",
                "choices": [
                    {"text": "Drink from the river", "next_scene": "river_drink"},
                    {"text": "Build a raft", "next_scene": "raft_build"},
                    {"text": "Return to forest", "next_scene": "forest_start"}
                ],
                "items": ["water_bottle"]
            },
            "treasure_room": {
                "description": "You found a treasure room! Inside you see gold coins and a magical sword.",
                "choices": [
                    {"text": "Take the sword", "next_scene": "treasure_taken"},
                    {"text": "Take some gold", "next_scene": "treasure_taken"},
                    {"text": "Leave everything", "next_scene": "cave"}
                ],
                "items": ["sword", "gold_coins"]
            },
            "treasure_taken": {
                "description": "You took some treasures but the cave started shaking. You quickly escape!",
                "choices": [
                    {"text": "Return to forest", "next_scene": "forest_start"}
                ],
                "items": []
            },
            "market": {
                "description": "The market is bustling with activity. Vendors sell various items.",
                "choices": [
                    {"text": "Buy health potion", "next_scene": "market_buy"},
                    {"text": "Buy food", "next_scene": "market_buy"},
                    {"text": "Leave market", "next_scene": "village"}
                ],
                "items": []
            },
            "market_buy": {
                "description": "You bought some supplies. Your inventory has been updated.",
                "choices": [
                    {"text": "Return to village", "next_scene": "village"}
                ],
                "items": ["health_potion", "bread"]
            },
            "village_talk": {
                "description": "The villagers tell you about an ancient dragon that lives in the mountains to the north.",
                "choices": [
                    {"text": "Head to the mountains", "next_scene": "mountains"},
                    {"text": "Stay in village", "next_scene": "village"}
                ],
                "items": []
            },
            "river_drink": {
                "description": "You drink from the clear river and feel refreshed. Your health improves slightly.",
                "choices": [
                    {"text": "Return to forest", "next_scene": "forest_start"}
                ],
                "items": []
            },
            "raft_build": {
                "description": "You build a sturdy raft and cross the river safely. You discover a hidden path on the other side.",
                "choices": [
                    {"text": "Follow the hidden path", "next_scene": "hidden_cave"},
                    {"text": "Return to forest", "next_scene": "forest_start"}
                ],
                "items": []
            },
            "hidden_cave": {
                "description": "The hidden path leads to a secret cave filled with ancient artifacts.",
                "choices": [
                    {"text": "Explore the artifacts", "next_scene": "artifact_room"},
                    {"text": "Exit the cave", "next_scene": "forest_start"}
                ],
                "items": ["ancient_artifact"]
            },
            "artifact_room": {
                "description": "You've discovered a room full of ancient artifacts. One artifact glows with power!",
                "choices": [
                    {"text": "Take the glowing artifact", "next_scene": "artifact_taken"},
                    {"text": "Leave it alone", "next_scene": "hidden_cave"}
                ],
                "items": ["glowing_artifact"]
            },
            "artifact_taken": {
                "description": "As you touch the artifact, it pulses with energy and grants you incredible strength!",
                "choices": [
                    {"text": "Continue your adventure", "next_scene": "forest_start"}
                ],
                "items": []
            },
            "mountains": {
                "description": "You climb the snowy mountains. At the peak, you see the ancient dragon sleeping.",
                "choices": [
                    {"text": "Try to sneak past", "next_scene": "sneak_attempt"},
                    {"text": "Attack the dragon", "next_scene": "dragon_battle"},
                    {"text": "Return to village", "next_scene": "village"}
                ],
                "items": []
            },
            "sneak_attempt": {
                "description": "You try to sneak past the dragon but accidentally wake it up! It roars in anger.",
                "choices": [
                    {"text": "Run away", "next_scene": "run_away"},
                    {"text": "Fight the dragon", "next_scene": "dragon_battle"}
                ],
                "items": []
            },
            "dragon_battle": {
                "description": "You fight the dragon with all your might. With the help of your new powers, you defeat it!",
                "choices": [
                    {"text": "Victory! Return to village", "next_scene": "victory"}
                ],
                "items": []
            },
            "run_away": {
                "description": "You run as fast as you can from the angry dragon. You escape safely but lose your strength.",
                "choices": [
                    {"text": "Return to village", "next_scene": "village"}
                ],
                "items": []
            },
            "victory": {
                "description": "Congratulations! You have defeated the dragon and saved the kingdom! Your heroic deeds are remembered forever.",
                "choices": [
                    {"text": "Play again", "next_scene": "forest_start"}
                ],
                "items": []
            }
        }

    def draw(self):
        screen.fill(WHITE)

        # Draw scene description
        scene = self.scenes[self.current_scene]
        desc_lines = scene["description"].split(". ")

        y_offset = 50
        for i, line in enumerate(desc_lines):
            if line.strip():
                text = font.render(line + (". " if i < len(desc_lines)-1 else ""), True, BLACK)
                screen.blit(text, (50, y_offset + i*40))

        # Draw choices
        y_offset = 300
        for i, choice in enumerate(scene["choices"]):
            text = small_font.render(f"{i+1}. {choice['text']}", True, BLACK)
            screen.blit(text, (50, y_offset + i*30))

        # Draw player stats
        stats_y = 450
        health_text = small_font.render(f"Health: {self.player.health}", True, BLACK)
        screen.blit(health_text, (50, stats_y))

        inventory_text = small_font.render(f"Inventory: {', '.join(self.player.inventory) or 'Empty'}", True, BLACK)
        screen.blit(inventory_text, (50, stats_y + 30))

        # Draw instructions
        instructions = [
            "Use number keys 1-3 to make choices",
            "Press R to restart game"
        ]

        for i, instruction in enumerate(instructions):
            text = small_font.render(instruction, True, BLACK)
            screen.blit(text, (SCREEN_WIDTH - 250, 10 + i*20))

    def handle_input(self, key):
        if self.game_state != "playing":
            return

        # Handle number input for choices
        if pygame.K_1 <= key <= pygame.K_3:
            choice_index = key - pygame.K_1
            scene = self.scenes[self.current_scene]
            if 0 <= choice_index < len(scene["choices"]):
                next_scene = scene["choices"][choice_index]["next_scene"]
                self.current_scene = next_scene

                # Add any items to inventory if they exist
                if "items" in scene and scene["items"]:
                    for item in scene["items"]:
                        if item not in self.player.inventory:
                            self.player.inventory.append(item)

def main():
    game = AdventureGame()

    running = True
    while running:
        clock.tick(FPS)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Restart game
                    game = AdventureGame()
                else:
                    game.handle_input(event.key)

        # Draw everything
        game.draw()

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    print("Starting Adventure Game...")
    try:
        main()
    except Exception as e:
        print(f"Error running game: {e}")
        sys.exit(1)