# ui.py
"""User interface helpers for Deepvault Survey roguelike.
Renders HUD, message log, and simple overlays on the pygame screen.
"""
import pygame
from typing import List

class UI:
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, small_font: pygame.font.Font):
        self.screen = screen
        self.font = font
        self.small_font = small_font
        self.log: List[str] = []  # recent messages, max 5
        self.max_log = 5

    def log_message(self, msg: str):
        self.log.append(msg)
        if len(self.log) > self.max_log:
            self.log.pop(0)

    def draw_hud(self, game):
        # Draw HP, depth, seed, flare timer, inventory slots
        hp_text = self.small_font.render(f"HP: {game.player.hp}/{game.player.max_hp}", True, (255, 255, 255))
        self.screen.blit(hp_text, (5, game.MAP_HEIGHT * game.TILE_SIZE + 5))
        depth_text = self.small_font.render(f"Depth: {game.dungeon.current_floor}/3", True, (255, 255, 255))
        self.screen.blit(depth_text, (100, game.MAP_HEIGHT * game.TILE_SIZE + 5))
        seed_text = self.small_font.render(f"Seed: {game.seed}", True, (255, 255, 255))
        self.screen.blit(seed_text, (200, game.MAP_HEIGHT * game.TILE_SIZE + 5))
        if game.flare_timer > 0:
            flare_text = self.small_font.render(f"Flare: {game.flare_timer}", True, (255, 255, 0))
            self.screen.blit(flare_text, (350, game.MAP_HEIGHT * game.TILE_SIZE + 5))
        # Inventory slots
        for i, item in enumerate(game.inventory.slots):
            slot_x = 500 + i * 30
            slot_rect = pygame.Rect(slot_x, game.MAP_HEIGHT * game.TILE_SIZE + 2, 28, 28)
            pygame.draw.rect(self.screen, (80, 80, 80), slot_rect, 2)
            if item:
                glyph = self.small_font.render(item.glyph, True, (200, 200, 0))
                self.screen.blit(glyph, (slot_x + 4, game.MAP_HEIGHT * game.TILE_SIZE + 6))
            # number label
            num = self.small_font.render(str(i + 1), True, (150, 150, 150))
            self.screen.blit(num, (slot_x - 12, game.MAP_HEIGHT * game.TILE_SIZE + 6))
        # Message log
        for idx, line in enumerate(reversed(self.log)):
            log_surf = self.small_font.render(line, True, (200, 200, 200))
            self.screen.blit(log_surf, (5, game.MAP_HEIGHT * game.TILE_SIZE + 30 + idx * 16))

    def draw_overlay(self, text: str):
        # Darken screen and show centered text
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        lines = text.split("\n")
        for i, line in enumerate(lines):
            surf = self.font.render(line, True, (255, 255, 255))
            rect = surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + i * 30))
            self.screen.blit(surf, rect)
