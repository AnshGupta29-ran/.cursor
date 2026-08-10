"""Pygame front-end for Viper Trace: menus, rendering, HUD, overlays.

Palette: deep ink background, vivid green snake, amber accent (food/path).
"""
from __future__ import annotations

import sys
from typing import Optional

import pygame

from .ai import AIStatus
from .config import DIFFICULTIES, Difficulty
from .engine import GameEngine, MODE_AI, MODE_MANUAL
from . import persistence

# ------------------------------------------------------------------ palette
BG = (13, 17, 23)
PANEL = (22, 27, 34)
GRID_LINE = (30, 36, 45)
WALL = (88, 99, 117)
SNAKE_HEAD = (63, 224, 120)
SNAKE_BODY = (35, 150, 85)
FOOD = (255, 171, 46)
ACCENT = (255, 171, 46)
PATH = (255, 210, 90)
EXPLORED = (60, 90, 130)
TEXT = (220, 228, 238)
DIM = (140, 152, 168)
DANGER = (240, 84, 84)

CELL = 24
HUD_H = 64
HELP_H = 28

KEY_DIRS = {
    pygame.K_UP: "UP", pygame.K_w: "UP",
    pygame.K_DOWN: "DOWN", pygame.K_s: "DOWN",
    pygame.K_LEFT: "LEFT", pygame.K_a: "LEFT",
    pygame.K_RIGHT: "RIGHT", pygame.K_d: "RIGHT",
}


class ViperTraceApp:
    """Menu / play / pause / game-over state machine."""

    def __init__(self, seed: Optional[int] = None):
        pygame.init()
        pygame.display.set_caption("Viper Trace — A* Snake Observatory")
        self.font = pygame.font.Font(None, 28)
        self.big_font = pygame.font.Font(None, 56)
        self.small_font = pygame.font.Font(None, 20)
        self.clock = pygame.time.Clock()
        self.seed = seed
        self.settings = persistence.load_settings()
        self.state = "menu"
        self.mode = MODE_MANUAL
        self.difficulty: Difficulty = DIFFICULTIES[
            self.settings.get("difficulty", "hatchling")
        ]
        self.menu_index = 0
        self.diff_index = list(DIFFICULTIES).index(self.difficulty.name.lower())
        self.engine: Optional[GameEngine] = None
        self.show_explored = bool(self.settings.get("show_explored", True))
        self.new_best = False
        self.screen: Optional[pygame.Surface] = None
        self._resize()

    # -------------------------------------------------------------- helpers
    def _resize(self) -> None:
        w = self.difficulty.width * CELL
        h = self.difficulty.height * CELL + HUD_H + HELP_H
        self.screen = pygame.display.set_mode((w, h))

    def _text(self, s, font, color, x, y, center=False):
        surf = font.render(s, True, color)
        rect = surf.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(surf, rect)

    def _start_run(self) -> None:
        saved_speed = self.settings.get("speed", {}).get(self.difficulty.name)
        self.engine = GameEngine(self.difficulty, self.mode, seed=self.seed, speed=saved_speed)
        self.new_best = False
        self.state = "playing"
        self._resize()

    def _persist_settings(self) -> None:
        if self.engine is not None:
            speeds = dict(self.settings.get("speed", {}))
            speeds[self.difficulty.name] = self.engine.speed
            self.settings["speed"] = speeds
        self.settings["difficulty"] = self.difficulty.name.lower()
        self.settings["show_explored"] = self.show_explored
        persistence.save_settings(self.settings)

    # ------------------------------------------------------------- rendering
    def _cell_rect(self, cell):
        return pygame.Rect(cell[0] * CELL, HUD_H + cell[1] * CELL, CELL, CELL)

    def _draw_menu(self) -> None:
        self.screen.fill(BG)
        w = self.screen.get_width()
        self._text("VIPER TRACE", self.big_font, SNAKE_HEAD, w // 2, 70, center=True)
        self._text("A* Snake Observatory", self.font, DIM, w // 2, 110, center=True)
        options = ["Manual Mode", "AI Mode (Trace Engine)", "Quit"]
        for i, opt in enumerate(options):
            color = ACCENT if i == self.menu_index else TEXT
            marker = "> " if i == self.menu_index else "  "
            self._text(marker + opt, self.font, color, w // 2 - 130, 180 + i * 36)
        diffs = list(DIFFICULTIES.values())
        d = diffs[self.diff_index]
        self._text(
            f"Difficulty: < {d.name} >   ({d.width}x{d.height}, {len(d.obstacle_coords)} walls, x{d.score_multiplier})",
            self.font, ACCENT, w // 2, 310, center=True)
        best_m = persistence.get_best(d.name, MODE_MANUAL)
        best_a = persistence.get_best(d.name, MODE_AI)
        self._text(f"Best — manual: {best_m}   ai: {best_a}", self.small_font, DIM, w // 2, 344, center=True)
        self._text("Up/Down select · Left/Right difficulty · Enter start", self.small_font, DIM, w // 2, 400, center=True)

    def _draw_play(self) -> None:
        eng = self.engine
        self.screen.fill(BG)
        # grid
        for x in range(self.difficulty.width + 1):
            pygame.draw.line(self.screen, GRID_LINE, (x * CELL, HUD_H), (x * CELL, HUD_H + self.difficulty.height * CELL))
        for y in range(self.difficulty.height + 1):
            pygame.draw.line(self.screen, GRID_LINE, (0, HUD_H + y * CELL), (self.difficulty.width * CELL, HUD_H + y * CELL))
        # obstacles
        for cell in self.difficulty.obstacle_coords:
            pygame.draw.rect(self.screen, WALL, self._cell_rect(cell))
        # explored tint
        if eng.mode == MODE_AI and self.show_explored:
            tint = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
            tint.fill((*EXPLORED, 70))
            for cell in eng.ai_closed:
                self.screen.blit(tint, self._cell_rect(cell).topleft)
        # planned path
        if eng.mode == MODE_AI and eng.ai_path:
            path_color = PATH if eng.ai_status is AIStatus.SAFE_ROUTE else DANGER
            pts = [
                (c[0] * CELL + CELL // 2, HUD_H + c[1] * CELL + CELL // 2)
                for c in [eng.snake.head] + eng.ai_path
            ]
            if len(pts) > 1:
                pygame.draw.lines(self.screen, path_color, False, pts, 3)
            for p in pts[1:]:
                pygame.draw.circle(self.screen, path_color, p, 3)
        # food
        if eng.food is not None:
            r = self._cell_rect(eng.food)
            pygame.draw.circle(self.screen, FOOD, r.center, CELL // 3)
        # snake
        for i, cell in enumerate(eng.snake.body):
            color = SNAKE_HEAD if i == 0 else SNAKE_BODY
            rect = self._cell_rect(cell).inflate(-2, -2)
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
        # HUD
        pygame.draw.rect(self.screen, PANEL, (0, 0, self.screen.get_width(), HUD_H))
        status_color = {
            AIStatus.SAFE_ROUTE: SNAKE_HEAD,
            AIStatus.SURVIVAL_WANDER: ACCENT,
            AIStatus.NO_PATH: DANGER,
        }.get(eng.ai_status, TEXT)
        self._text(f"Score {eng.score}", self.font, TEXT, 10, 8)
        self._text(f"Len {eng.length}", self.font, TEXT, 10, 34)
        self._text(f"{eng.mode.upper()} · {self.difficulty.name}", self.font, TEXT, 130, 8)
        self._text(f"Speed {eng.speed}", self.font, TEXT, 130, 34)
        self._text(eng.hud_status, self.font, status_color, 320, 8)
        self._text(f"Pellets {eng.pellets}  Ticks {eng.ticks}", self.small_font, DIM, 320, 36)
        # help line
        help_y = HUD_H + self.difficulty.height * CELL
        pygame.draw.rect(self.screen, PANEL, (0, help_y, self.screen.get_width(), HELP_H))
        self._text(
            "Arrows/WASD move · P pause · +/- speed · T explored tint · R restart · Esc menu",
            self.small_font, DIM, 10, help_y + 6)

    def _draw_center_overlay(self, title, lines, title_color=ACCENT):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))
        w, h = self.screen.get_size()
        self._text(title, self.big_font, title_color, w // 2, h // 2 - 60, center=True)
        for i, line in enumerate(lines):
            self._text(line, self.font, TEXT, w // 2, h // 2 + i * 30, center=True)

    def _draw_pause(self) -> None:
        self._draw_play()
        self._draw_center_overlay("PAUSED", ["P resume · Esc menu"])

    def _draw_game_over(self) -> None:
        self._draw_play()
        eng = self.engine
        best = persistence.get_best(self.difficulty.name, eng.mode)
        title = "BOARD FULL — YOU WIN" if eng.won else "GAME OVER"
        color = SNAKE_HEAD if eng.won else DANGER
        lines = [
            f"Score {eng.score}   Best {best}" + ("   NEW BEST!" if self.new_best else ""),
        ]
        if eng.mode == MODE_AI:
            lines.append(f"Pellets {eng.pellets} · Ticks survived {eng.ticks} · Fallbacks {eng.fallback_count}")
        lines.append("R restart · Esc menu")
        self._draw_center_overlay(title, lines, color)

    # ---------------------------------------------------------------- states
    def _handle_menu_key(self, key) -> None:
        diffs = list(DIFFICULTIES.keys())
        if key in (pygame.K_UP, pygame.K_w):
            self.menu_index = (self.menu_index - 1) % 3
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.menu_index = (self.menu_index + 1) % 3
        elif key == pygame.K_LEFT:
            self.diff_index = (self.diff_index - 1) % len(diffs)
            self.difficulty = DIFFICULTIES[diffs[self.diff_index]]
            self._resize()
        elif key == pygame.K_RIGHT:
            self.diff_index = (self.diff_index + 1) % len(diffs)
            self.difficulty = DIFFICULTIES[diffs[self.diff_index]]
            self._resize()
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.menu_index == 0:
                self.mode = MODE_MANUAL
                self._start_run()
            elif self.menu_index == 1:
                self.mode = MODE_AI
                self._start_run()
            else:
                self._quit()

    def _handle_play_key(self, key) -> None:
        eng = self.engine
        if key in KEY_DIRS and eng.mode == MODE_MANUAL:
            eng.queue_direction(KEY_DIRS[key])
        elif key == pygame.K_p:
            self.state = "paused"
        elif key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            eng.adjust_speed(1)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            eng.adjust_speed(-1)
        elif key == pygame.K_t:
            self.show_explored = not self.show_explored
        elif key == pygame.K_r:
            self._start_run()
        elif key == pygame.K_ESCAPE:
            self._persist_settings()
            self.state = "menu"

    def _handle_game_over_key(self, key) -> None:
        if key == pygame.K_r:
            self._start_run()
        elif key == pygame.K_ESCAPE:
            self._persist_settings()
            self.state = "menu"

    def _quit(self) -> None:
        self._persist_settings()
        pygame.quit()
        sys.exit(0)

    # -------------------------------------------------------------- mainloop
    def run(self) -> None:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                elif event.type == pygame.KEYDOWN:
                    if self.state == "menu":
                        self._handle_menu_key(event.key)
                    elif self.state == "playing":
                        self._handle_play_key(event.key)
                    elif self.state == "paused":
                        if event.key == pygame.K_p:
                            self.state = "playing"
                        elif event.key == pygame.K_ESCAPE:
                            self._persist_settings()
                            self.state = "menu"
                    elif self.state == "game_over":
                        self._handle_game_over_key(event.key)

            if self.state == "menu":
                self._draw_menu()
                self.clock.tick(30)
            elif self.state == "playing":
                self.engine.tick()
                if not self.engine.alive or self.engine.won:
                    self.new_best = persistence.save_best(
                        self.difficulty.name, self.engine.mode, self.engine.score
                    )
                    self._persist_settings()
                    self.state = "game_over"
                self._draw_play()
                self.clock.tick(self.engine.speed)
            elif self.state == "paused":
                self._draw_pause()
                self.clock.tick(30)
            elif self.state == "game_over":
                self._draw_game_over()
                self.clock.tick(30)

            pygame.display.flip()
