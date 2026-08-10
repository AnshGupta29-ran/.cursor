"""All pygame rendering for Core Tap. Pure drawing; no game rules here."""
from __future__ import annotations

import pygame

from ..core.constants import (
    BRICK_SPECS, COL_ACCENT, COL_BG, COL_BG2, COL_MODULE, COL_PULSE, COL_RIG,
    COL_TEXT, COL_WARN, HEIGHT, M_DRAG, M_PIERCE, PULSE_RADIUS, RIG_HEIGHT,
    RIG_Y, WIDTH,
)
from ..core.engine import Game

_FONT_CACHE: dict[int, pygame.font.Font] = {}


def font(size: int) -> pygame.font.Font:
    if size not in _FONT_CACHE:
        _FONT_CACHE[size] = pygame.font.SysFont("consolas", size)
    return _FONT_CACHE[size]


def text(surf, s, size, color, x, y, center=False):
    img = font(size).render(s, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surf.blit(img, rect)
    return rect


def _brick_glyph(cls: str) -> str:
    return {"sediment": "~", "ore": "*", "core": "O", "basalt": "#"}[cls]


def draw_bricks(surf, game: Game) -> None:
    for b in game.bricks:
        spec = BRICK_SPECS[b.cls]
        color = spec["color"]
        rect = pygame.Rect(int(b.x), int(b.y), int(b.w), int(b.h))
        pygame.draw.rect(surf, color, rect, border_radius=4)
        pygame.draw.rect(surf, tuple(min(255, c + 40) for c in color), rect,
                         width=1, border_radius=4)
        # core visibly cracks as hits decrease
        if b.cls == "core":
            max_hits = spec["hits"]
            cracked = max_hits - b.hits_left
            for i in range(cracked):
                x0 = rect.x + 6 + i * 12
                pygame.draw.line(surf, (20, 10, 30), (x0, rect.y + 2),
                                 (x0 + 8, rect.bottom - 2), 2)
        glyph = _brick_glyph(b.cls)
        text(surf, glyph, 14, (10, 15, 25), rect.centerx, rect.centery, True)


def draw_rig(surf, game: Game) -> None:
    w = game.rig_width
    rect = pygame.Rect(int(game.rig_x - w / 2), RIG_Y, int(w), RIG_HEIGHT)
    pygame.draw.rect(surf, COL_RIG, rect, border_radius=6)
    pygame.draw.rect(surf, COL_ACCENT, rect, width=2, border_radius=6)
    # survey light
    pygame.draw.circle(surf, COL_ACCENT,
                       (int(game.rig_x), RIG_Y + RIG_HEIGHT // 2), 4)


def draw_pulses(surf, game: Game) -> None:
    for p in game.pulses:
        pygame.draw.circle(surf, COL_PULSE, (int(p.x), int(p.y)), PULSE_RADIUS)
        pygame.draw.circle(surf, COL_ACCENT, (int(p.x), int(p.y)),
                           PULSE_RADIUS, 1)


MODULE_BADGES = {
    "wide_rig": ("W", (0, 188, 212)),
    "split_pulse": ("S", (255, 214, 64)),
    "drag_field": ("D", (130, 177, 255)),
    "pierce_charge": ("P", (255, 110, 64)),
    "spare_hull": ("+", (105, 240, 174)),
}


def draw_drops(surf, game: Game) -> None:
    for d in game.drops:
        badge, color = MODULE_BADGES[d.kind]
        rect = pygame.Rect(int(d.x - 14), int(d.y - 9), 28, 18)
        pygame.draw.rect(surf, color, rect, border_radius=4)
        text(surf, badge, 13, (5, 15, 25), rect.centerx, rect.centery, True)


def draw_hud(surf, game: Game) -> None:
    pygame.draw.rect(surf, COL_BG2, (0, 0, WIDTH, 44))
    text(surf, f"ORE {game.score:06d}", 18, COL_TEXT, 12, 12)
    text(surf, f"HULLS {'|'*game.hulls if game.hulls else '-'}", 18,
         COL_WARN if game.hulls <= 1 else COL_TEXT, 190, 12)
    text(surf, f"SITE {game.site_index+1}/{len(game.sites)} "
               f"{game.site.name} {game.site.depth_m}m", 18, COL_TEXT, 330, 12)
    x = WIDTH - 16
    for kind, secs in sorted(game.timers.items()):
        badge, color = MODULE_BADGES[kind]
        s = f"[{badge}]{int(secs)+1}s"
        rect = text(surf, s, 15, color, x, 14)
        x -= rect.width + 14
        x -= 0
    if M_DRAG in game.timers:
        pass


def draw_scene(surf, game: Game) -> None:
    surf.fill(COL_BG)
    # abyssal gradient bands
    for i in range(6):
        shade = tuple(max(0, c - i * 2) for c in COL_BG2)
        pygame.draw.rect(surf, shade, (0, HEIGHT - i * 100, WIDTH, 100))
    draw_bricks(surf, game)
    draw_drops(surf, game)
    draw_rig(surf, game)
    draw_pulses(surf, game)
    draw_hud(surf, game)


def overlay(surf, lines: list[tuple[str, int, tuple]], title: str) -> None:
    veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    veil.fill((4, 12, 24, 210))
    surf.blit(veil, (0, 0))
    text(surf, title, 40, COL_ACCENT, WIDTH // 2, 140, True)
    y = 220
    for s, size, color in lines:
        text(surf, s, size, color, WIDTH // 2, y, True)
        y += size + 12
