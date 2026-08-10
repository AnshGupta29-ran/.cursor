#!/usr/bin/env python3
"""Fathom Fields — clickable Minesweeper with deduction hints (pygame)."""

from __future__ import annotations

import random
import sys
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Set, Tuple

import pygame

Cell = Tuple[int, int]

# --- presets -----------------------------------------------------------------
PRESETS = {
    "rowboat": ("Rowboat", 9, 9, 10),
    "trawler": ("Trawler", 16, 16, 40),
    "freighter": ("Freighter", 16, 30, 99),
}

THEMES = {
    "daylight": {
        "bg": (18, 42, 58),
        "hud": (12, 28, 40),
        "panel": (28, 58, 78),
        "hidden": (62, 110, 138),
        "hidden_hi": (78, 130, 160),
        "swept": (210, 224, 230),
        "grid": (24, 48, 64),
        "text": (240, 246, 250),
        "muted": (160, 190, 205),
        "hazard": (200, 60, 55),
        "mark": (230, 90, 70),
        "hint": (255, 200, 60),
        "win": (70, 180, 120),
        "btn": (40, 90, 120),
        "btn_hi": (55, 120, 155),
        "nums": [
            (0, 0, 0),
            (30, 90, 200),
            (30, 140, 70),
            (190, 50, 50),
            (80, 40, 160),
            (150, 60, 30),
            (20, 140, 140),
            (40, 40, 40),
            (100, 100, 100),
        ],
    },
    "night": {
        "bg": (10, 12, 22),
        "hud": (6, 8, 16),
        "panel": (22, 26, 42),
        "hidden": (40, 48, 72),
        "hidden_hi": (55, 65, 95),
        "swept": (28, 32, 48),
        "grid": (14, 16, 28),
        "text": (220, 225, 240),
        "muted": (130, 140, 170),
        "hazard": (220, 70, 90),
        "mark": (255, 140, 80),
        "hint": (255, 210, 80),
        "win": (80, 200, 140),
        "btn": (50, 55, 90),
        "btn_hi": (70, 80, 120),
        "nums": [
            (0, 0, 0),
            (100, 160, 255),
            (90, 210, 130),
            (255, 100, 110),
            (180, 130, 255),
            (255, 160, 90),
            (90, 210, 210),
            (200, 200, 220),
            (150, 150, 170),
        ],
    },
    "signal": {
        "bg": (28, 20, 18),
        "hud": (18, 12, 10),
        "panel": (48, 32, 28),
        "hidden": (180, 70, 55),
        "hidden_hi": (200, 95, 70),
        "swept": (245, 230, 210),
        "grid": (40, 24, 20),
        "text": (255, 245, 235),
        "muted": (210, 180, 160),
        "hazard": (40, 40, 40),
        "mark": (255, 210, 40),
        "hint": (80, 200, 255),
        "win": (60, 170, 100),
        "btn": (120, 50, 40),
        "btn_hi": (150, 70, 55),
        "nums": [
            (0, 0, 0),
            (20, 60, 180),
            (20, 120, 50),
            (180, 30, 30),
            (90, 30, 140),
            (140, 70, 20),
            (20, 120, 120),
            (30, 30, 30),
            (90, 90, 90),
        ],
    },
}

THEME_KEYS = list(THEMES.keys())


class SessionState(Enum):
    MENU = auto()
    READY = auto()
    RUNNING = auto()
    WON = auto()
    LOST = auto()


@dataclass
class HintResult:
    kind: str  # SafeWater | CertainHazard | NoForcedMove
    cells: List[Cell]
    reason: str


class Chart:
    """Pure board logic — no UI."""

    def __init__(self, rows: int, cols: int, hazards: int, seed: int | None = None):
        self.rows = rows
        self.cols = cols
        self.hazard_count = hazards
        self.seed = seed if seed is not None else random.randrange(1 << 30)
        self.rng = random.Random(self.seed)
        self.has_hazard = [[False] * cols for _ in range(rows)]
        self.adjacent = [[0] * cols for _ in range(rows)]
        self.swept = [[False] * cols for _ in range(rows)]
        self.marked = [[False] * cols for _ in range(rows)]
        self.placed = False
        self.state = SessionState.READY
        self.hints_used = 0
        self.started_at: Optional[float] = None
        self.elapsed = 0.0
        self.hint: Optional[HintResult] = None

    def neighbors(self, r: int, c: int) -> List[Cell]:
        out: List[Cell] = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    out.append((nr, nc))
        return out

    def marks_remaining(self) -> int:
        marks = sum(1 for r in range(self.rows) for c in range(self.cols) if self.marked[r][c])
        return self.hazard_count - marks

    def _place(self, safe_r: int, safe_c: int) -> None:
        protected: Set[Cell] = {(safe_r, safe_c), *self.neighbors(safe_r, safe_c)}
        candidates = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) not in protected
        ]
        self.rng.shuffle(candidates)
        for r, c in candidates[: self.hazard_count]:
            self.has_hazard[r][c] = True
        for r in range(self.rows):
            for c in range(self.cols):
                if self.has_hazard[r][c]:
                    self.adjacent[r][c] = -1
                else:
                    self.adjacent[r][c] = sum(
                        1 for nr, nc in self.neighbors(r, c) if self.has_hazard[nr][nc]
                    )
        self.placed = True

    def sweep(self, r: int, c: int) -> None:
        if self.state in (SessionState.WON, SessionState.LOST):
            return
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return
        if self.marked[r][c] or self.swept[r][c]:
            return
        if not self.placed:
            self._place(r, c)
            self.state = SessionState.RUNNING
            self.started_at = time.time()
        if self.has_hazard[r][c]:
            self.swept[r][c] = True
            self.state = SessionState.LOST
            self._freeze_time()
            self._reveal_all_hazards()
            return
        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            if self.swept[cr][cc] or self.marked[cr][cc]:
                continue
            self.swept[cr][cc] = True
            if self.adjacent[cr][cc] == 0:
                for nr, nc in self.neighbors(cr, cc):
                    if not self.swept[nr][nc] and not self.marked[nr][nc]:
                        stack.append((nr, nc))
        self.hint = None
        self._check_win()

    def toggle_mark(self, r: int, c: int) -> None:
        if self.state in (SessionState.WON, SessionState.LOST):
            return
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return
        if self.swept[r][c]:
            return
        if not self.marked[r][c] and self.marks_remaining() <= 0:
            return
        self.marked[r][c] = not self.marked[r][c]
        self.hint = None

    def chord(self, r: int, c: int) -> None:
        if self.state not in (SessionState.RUNNING, SessionState.READY):
            return
        if not self.swept[r][c] or self.adjacent[r][c] <= 0:
            return
        marks = sum(1 for nr, nc in self.neighbors(r, c) if self.marked[nr][nc])
        if marks != self.adjacent[r][c]:
            return
        for nr, nc in self.neighbors(r, c):
            if not self.marked[nr][nc] and not self.swept[nr][nc]:
                self.sweep(nr, nc)
                if self.state == SessionState.LOST:
                    return

    def request_hint(self) -> HintResult:
        result = self._compute_hint()
        if result.kind != "NoForcedMove":
            self.hints_used += 1
        self.hint = result
        return result

    def _compute_hint(self) -> HintResult:
        if not self.placed:
            return HintResult("NoForcedMove", [], "Sweep a cell first — then the Hint Buoy can deduce.")

        # Rule 1: satisfied number ⇒ remaining hidden neighbors are SafeWater
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.swept[r][c] or self.adjacent[r][c] <= 0:
                    continue
                neigh = self.neighbors(r, c)
                marks = [(nr, nc) for nr, nc in neigh if self.marked[nr][nc]]
                hidden = [
                    (nr, nc)
                    for nr, nc in neigh
                    if not self.swept[nr][nc] and not self.marked[nr][nc]
                ]
                if len(marks) == self.adjacent[r][c] and hidden:
                    cell = hidden[0]
                    return HintResult(
                        "SafeWater",
                        [cell],
                        f"All {self.adjacent[r][c]} hazards around ({r},{c}) are marked → ({cell[0]},{cell[1]}) is safe water.",
                    )

        # Rule 2: number − marks == hidden count ⇒ all hidden are CertainHazard
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.swept[r][c] or self.adjacent[r][c] <= 0:
                    continue
                neigh = self.neighbors(r, c)
                marks = sum(1 for nr, nc in neigh if self.marked[nr][nc])
                hidden = [
                    (nr, nc)
                    for nr, nc in neigh
                    if not self.swept[nr][nc] and not self.marked[nr][nc]
                ]
                need = self.adjacent[r][c] - marks
                if need > 0 and need == len(hidden):
                    cell = hidden[0]
                    return HintResult(
                        "CertainHazard",
                        [cell],
                        f"({r},{c}) needs {need} more hazard(s) among {len(hidden)} hidden → ({cell[0]},{cell[1]}) is a hazard — mark it.",
                    )

        # Rule 3 (subset): if A's hidden ⊂ B's and counts equal, B\\A is safe
        constraints: List[Tuple[Set[Cell], int, Cell]] = []
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.swept[r][c] or self.adjacent[r][c] <= 0:
                    continue
                neigh = self.neighbors(r, c)
                marks = sum(1 for nr, nc in neigh if self.marked[nr][nc])
                hidden = {
                    (nr, nc)
                    for nr, nc in neigh
                    if not self.swept[nr][nc] and not self.marked[nr][nc]
                }
                need = self.adjacent[r][c] - marks
                if hidden and need >= 0:
                    constraints.append((hidden, need, (r, c)))
        for ha, ca, pa in constraints:
            for hb, cb, pb in constraints:
                if pa == pb or not ha or not hb:
                    continue
                if ha < hb and ca == cb:
                    diff = hb - ha
                    if diff:
                        cell = next(iter(diff))
                        return HintResult(
                            "SafeWater",
                            [cell],
                            f"Subset rule: constraint at {pa} ⊂ {pb} with equal remaining → ({cell[0]},{cell[1]}) is safe.",
                        )

        return HintResult("NoForcedMove", [], "No forced move — the Hint Buoy has nothing certain yet.")

    def _check_win(self) -> None:
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.has_hazard[r][c] and not self.swept[r][c]:
                    return
        self.state = SessionState.WON
        self._freeze_time()

    def _reveal_all_hazards(self) -> None:
        for r in range(self.rows):
            for c in range(self.cols):
                if self.has_hazard[r][c]:
                    self.swept[r][c] = True

    def _freeze_time(self) -> None:
        if self.started_at is not None:
            self.elapsed = time.time() - self.started_at

    def tick(self) -> None:
        if self.state == SessionState.RUNNING and self.started_at is not None:
            self.elapsed = time.time() - self.started_at


# --- UI ----------------------------------------------------------------------

HUD_H = 56
LOG_H = 72
MARGIN = 12
CELL = 28
MENU_W, MENU_H = 720, 480


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Fathom Fields")
        self.theme_i = 0
        self.theme = THEMES[THEME_KEYS[self.theme_i]]
        self.preset_key = "rowboat"
        self.chart: Optional[Chart] = None
        self.state = SessionState.MENU
        self.font = pygame.font.SysFont("segoeui", 18)
        self.font_sm = pygame.font.SysFont("segoeui", 14)
        self.font_lg = pygame.font.SysFont("segoeui", 28, bold=True)
        self.font_cell = pygame.font.SysFont("consolas", 16, bold=True)
        self.pulse = 0.0
        self.screen = pygame.display.set_mode((MENU_W, MENU_H))
        self.clock = pygame.time.Clock()
        self.log_msg = "Welcome aboard. Pick a vessel class to chart the harbor."
        self._layout_menu_buttons()

    def _layout_menu_buttons(self) -> None:
        self.menu_btns: List[Tuple[pygame.Rect, str, str]] = []
        y = 180
        for key, (label, rows, cols, mines) in PRESETS.items():
            rect = pygame.Rect(MENU_W // 2 - 160, y, 320, 44)
            self.menu_btns.append((rect, key, f"{label}  —  {rows}×{cols}, {mines} hazards"))
            y += 56

    def new_game(self, preset_key: str) -> None:
        self.preset_key = preset_key
        label, rows, cols, mines = PRESETS[preset_key]
        self.chart = Chart(rows, cols, mines)
        self.state = SessionState.READY
        self.log_msg = f"{label} chart seeded ({self.chart.seed}). Left-click sweep · right-click mark · H hint."
        self._resize_for_board(rows, cols)

    def _resize_for_board(self, rows: int, cols: int) -> None:
        global CELL
        # Fit Freighter on screen without scrolling
        max_w = min(1280, pygame.display.Info().current_w - 40)
        max_h = min(900, pygame.display.Info().current_h - 80)
        cell_w = (max_w - 2 * MARGIN) // cols
        cell_h = (max_h - HUD_H - LOG_H - 2 * MARGIN) // rows
        CELL = max(16, min(36, cell_w, cell_h))
        w = cols * CELL + 2 * MARGIN
        h = rows * CELL + HUD_H + LOG_H + 2 * MARGIN
        self.screen = pygame.display.set_mode((w, h))

    def cycle_theme(self) -> None:
        self.theme_i = (self.theme_i + 1) % len(THEME_KEYS)
        self.theme = THEMES[THEME_KEYS[self.theme_i]]
        name = THEME_KEYS[self.theme_i]
        pretty = {"daylight": "Daylight Harbor", "night": "Night Watch", "signal": "Signal Flags"}[name]
        self.log_msg = f"Theme → {pretty}"

    def cell_at(self, pos: Tuple[int, int]) -> Optional[Cell]:
        if self.chart is None:
            return None
        x, y = pos
        gx = x - MARGIN
        gy = y - HUD_H - MARGIN
        if gx < 0 or gy < 0:
            return None
        c, r = gx // CELL, gy // CELL
        if 0 <= r < self.chart.rows and 0 <= c < self.chart.cols:
            return r, c
        return None

    def run(self) -> None:
        while True:
            dt = self.clock.tick(60) / 1000.0
            self.pulse = (self.pulse + dt) % 1.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                self._handle(event)
            if self.chart and self.state not in (SessionState.MENU,):
                self.chart.tick()
                if self.chart.state in (SessionState.WON, SessionState.LOST):
                    self.state = self.chart.state
            self._draw()
            pygame.display.flip()

    def _handle(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = SessionState.MENU
                self.chart = None
                self.screen = pygame.display.set_mode((MENU_W, MENU_H))
                self.log_msg = "Back to harbor menu."
                return
            if event.key == pygame.K_t:
                self.cycle_theme()
            if self.state == SessionState.MENU:
                return
            if event.key == pygame.K_r and self.chart:
                self.new_game(self.preset_key)
            if event.key == pygame.K_1:
                self.new_game("rowboat")
            if event.key == pygame.K_2:
                self.new_game("trawler")
            if event.key == pygame.K_3:
                self.new_game("freighter")
            if event.key == pygame.K_h and self.chart and self.state in (
                SessionState.READY,
                SessionState.RUNNING,
            ):
                hint = self.chart.request_hint()
                self.log_msg = hint.reason
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == SessionState.MENU:
                for rect, key, _ in self.menu_btns:
                    if rect.collidepoint(event.pos):
                        self.new_game(key)
                return
            if self.chart is None:
                return
            if self.state in (SessionState.WON, SessionState.LOST):
                return
            cell = self.cell_at(event.pos)
            if cell is None:
                return
            r, c = cell
            if event.button == 1:
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_SHIFT:
                    self.chart.chord(r, c)
                else:
                    self.chart.sweep(r, c)
                if self.chart.state == SessionState.RUNNING:
                    self.state = SessionState.RUNNING
                elif self.chart.state == SessionState.WON:
                    self.state = SessionState.WON
                    self.log_msg = f"Harbor cleared in {int(self.chart.elapsed)}s · hints {self.chart.hints_used}. Press R to rechart."
                elif self.chart.state == SessionState.LOST:
                    self.state = SessionState.LOST
                    self.log_msg = "Hazard struck — chart lost. Press R to restart."
            elif event.button == 3:
                self.chart.toggle_mark(r, c)

    def _draw(self) -> None:
        th = self.theme
        self.screen.fill(th["bg"])
        if self.state == SessionState.MENU:
            self._draw_menu()
            return
        self._draw_hud()
        self._draw_board()
        self._draw_log()
        if self.state == SessionState.WON:
            self._banner("CHART CLEARED", th["win"])
        elif self.state == SessionState.LOST:
            self._banner("HAZARD STRUCK", th["hazard"])

    def _draw_menu(self) -> None:
        th = self.theme
        title = self.font_lg.render("Fathom Fields", True, th["text"])
        self.screen.blit(title, title.get_rect(center=(MENU_W // 2, 80)))
        sub = self.font.render("Deduction-first harbor sweeping", True, th["muted"])
        self.screen.blit(sub, sub.get_rect(center=(MENU_W // 2, 120)))
        mx, my = pygame.mouse.get_pos()
        for rect, _, label in self.menu_btns:
            hi = rect.collidepoint(mx, my)
            pygame.draw.rect(self.screen, th["btn_hi"] if hi else th["btn"], rect, border_radius=8)
            pygame.draw.rect(self.screen, th["hint"] if hi else th["muted"], rect, 2, border_radius=8)
            txt = self.font.render(label, True, th["text"])
            self.screen.blit(txt, txt.get_rect(center=rect.center))
        tip = self.font_sm.render(
            "In-game: LMB sweep · RMB mark · Shift+LMB chord · H hint · T theme · 1/2/3 preset · R restart · Esc menu",
            True,
            th["muted"],
        )
        self.screen.blit(tip, tip.get_rect(center=(MENU_W // 2, MENU_H - 40)))

    def _draw_hud(self) -> None:
        th = self.theme
        assert self.chart is not None
        w = self.screen.get_width()
        pygame.draw.rect(self.screen, th["hud"], (0, 0, w, HUD_H))
        label = PRESETS[self.preset_key][0]
        theme_name = {"daylight": "Daylight", "night": "Night Watch", "signal": "Signal Flags"}[
            THEME_KEYS[self.theme_i]
        ]
        left = self.font.render(
            f"Fathom Fields  ·  {label}  ·  hazards left {self.chart.marks_remaining()}",
            True,
            th["text"],
        )
        self.screen.blit(left, (MARGIN, 10))
        right = self.font.render(
            f"time {int(self.chart.elapsed)}s  ·  hints {self.chart.hints_used}  ·  {theme_name}",
            True,
            th["muted"],
        )
        self.screen.blit(right, (MARGIN, 32))

    def _draw_board(self) -> None:
        th = self.theme
        assert self.chart is not None
        chart = self.chart
        hint_cells = set(chart.hint.cells) if chart.hint else set()
        ox, oy = MARGIN, HUD_H + MARGIN
        mx, my = pygame.mouse.get_pos()
        hover = self.cell_at((mx, my))

        for r in range(chart.rows):
            for c in range(chart.cols):
                x = ox + c * CELL
                y = oy + r * CELL
                rect = pygame.Rect(x, y, CELL - 1, CELL - 1)
                swept = chart.swept[r][c]
                marked = chart.marked[r][c]
                if swept:
                    color = th["swept"]
                elif hover == (r, c) and self.state in (SessionState.READY, SessionState.RUNNING):
                    color = th["hidden_hi"]
                else:
                    color = th["hidden"]
                pygame.draw.rect(self.screen, color, rect, border_radius=3)

                if (r, c) in hint_cells:
                    # pulsing buoy-gold outline
                    alpha_boost = int(80 + 100 * abs(0.5 - self.pulse) * 2)
                    outline = th["hint"]
                    pygame.draw.rect(self.screen, outline, rect, 3, border_radius=3)
                    # soft glow fill
                    glow = pygame.Surface((CELL - 1, CELL - 1), pygame.SRCALPHA)
                    glow.fill((*outline, min(120, alpha_boost)))
                    self.screen.blit(glow, rect.topleft)

                if swept:
                    if chart.has_hazard[r][c]:
                        pygame.draw.circle(
                            self.screen,
                            th["hazard"],
                            rect.center,
                            max(4, CELL // 4),
                        )
                    elif chart.adjacent[r][c] > 0:
                        n = chart.adjacent[r][c]
                        txt = self.font_cell.render(str(n), True, th["nums"][n])
                        self.screen.blit(txt, txt.get_rect(center=rect.center))
                elif marked:
                    # triangular mark pennant
                    cx, cy = rect.center
                    pts = [(cx, cy - CELL // 4), (cx + CELL // 4, cy), (cx, cy + CELL // 5)]
                    pygame.draw.polygon(self.screen, th["mark"], pts)
                    if self.state == SessionState.LOST and not chart.has_hazard[r][c]:
                        pygame.draw.line(
                            self.screen, th["text"], rect.topleft, rect.bottomright, 2
                        )

    def _draw_log(self) -> None:
        th = self.theme
        w, h = self.screen.get_size()
        y = h - LOG_H
        pygame.draw.rect(self.screen, th["panel"], (0, y, w, LOG_H))
        label = self.font_sm.render("Hint Buoy / log", True, th["muted"])
        self.screen.blit(label, (MARGIN, y + 8))
        # wrap reason
        words = self.log_msg.split()
        lines: List[str] = []
        cur = ""
        for word in words:
            trial = f"{cur} {word}".strip()
            if self.font.size(trial)[0] > w - 2 * MARGIN:
                if cur:
                    lines.append(cur)
                cur = word
            else:
                cur = trial
        if cur:
            lines.append(cur)
        for i, line in enumerate(lines[:2]):
            surf = self.font.render(line, True, th["text"])
            self.screen.blit(surf, (MARGIN, y + 28 + i * 20))

    def _banner(self, text: str, color: Tuple[int, int, int]) -> None:
        w, h = self.screen.get_size()
        overlay = pygame.Surface((w, 64), pygame.SRCALPHA)
        overlay.fill((*color, 200))
        self.screen.blit(overlay, (0, h // 2 - 32))
        surf = self.font_lg.render(text, True, (255, 255, 255))
        self.screen.blit(surf, surf.get_rect(center=(w // 2, h // 2)))


def _smoke() -> int:
    """Headless logic checks — no display required."""
    fails = 0
    # seeded reproducibility
    a, b = Chart(9, 9, 10, seed=42), Chart(9, 9, 10, seed=42)
    a.sweep(4, 4)
    b.sweep(4, 4)
    if a.has_hazard != b.has_hazard:
        print("FAIL seeded reproducibility")
        fails += 1
    else:
        print("PASS seeded reproducibility")

    # first-click safety
    safe_ok = True
    for s in range(20):
        g = Chart(9, 9, 10, seed=s)
        g.sweep(2, 2)
        if g.has_hazard[2][2] or any(g.has_hazard[nr][nc] for nr, nc in g.neighbors(2, 2)):
            safe_ok = False
            break
    print("PASS first-click safety" if safe_ok else "FAIL first-click safety")
    fails += 0 if safe_ok else 1

    # hint rule 1 on crafted board
    g = Chart(5, 5, 1, seed=1)
    g._place = lambda *a, **k: None  # type: ignore
    g.placed = True
    g.has_hazard = [[False] * 5 for _ in range(5)]
    g.has_hazard[0][0] = True
    g.adjacent = [[0] * 5 for _ in range(5)]
    for r in range(5):
        for c in range(5):
            g.adjacent[r][c] = sum(
                1 for nr, nc in g.neighbors(r, c) if g.has_hazard[nr][nc]
            )
    g.swept[1][1] = True
    g.marked[0][0] = True
    h = g._compute_hint()
    if h.kind == "SafeWater":
        print("PASS hint safe-water rule")
    else:
        print(f"FAIL hint safe-water rule ({h})")
        fails += 1

    print("SMOKE PASS" if fails == 0 else f"SMOKE FAIL ({fails})")
    return 1 if fails else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--smoke", "smoke"):
        raise SystemExit(_smoke())
    App().run()
