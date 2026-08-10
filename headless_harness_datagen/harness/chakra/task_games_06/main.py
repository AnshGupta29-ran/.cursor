#!/usr/bin/env python3
"""
Pegfall Lab — Python + pygame implementation.

Deterministic pachinko-board physics sandbox with per-peg hit histograms,
seeded RNG, SQLite persistence, and headless smoke mode.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sqlite3
import struct
import sys
import time
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple

import pygame

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BOARD_W = 800
BOARD_H = 600
FPS = 60
PHYSICS_HZ = 120
DT = 1.0 / PHYSICS_HZ

BALL_RADIUS = 8
PEG_RADIUS = 10
BALL_RESTITUTION = 0.5
PEG_RESTITUTION = 0.4
WALL_RESTITUTION = 0.5
MAX_BALLS = 32
MAX_PEGS = 64
MAX_SPEED_ZEROG = 300.0
SPAWN_JITTER_PX = 20

BG_COLOR = (18, 18, 30)
PEG_COLOR = (60, 60, 90)
PEG_HOT_MIN = (200, 80, 30)
PEG_HOT_MAX = (255, 60, 20)
BALL_COLOR = (220, 200, 80)
WALL_COLOR = (40, 40, 60)
HUD_COLOR = (180, 200, 210)
RED_FLASH_DURATION = 0.15  # seconds

# ---------------------------------------------------------------------------
# Seeded RNG (xorshift32)
# ---------------------------------------------------------------------------


class SeededRNG:
    """Deterministic xorshift32 PRNG."""

    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFF
        if self.state == 0:
            self.state = 1

    def next(self) -> int:
        x = self.state
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= (x >> 17) & 0xFFFFFFFF
        x ^= (x << 5) & 0xFFFFFFFF
        self.state = x
        return x

    def next_float(self) -> float:
        return (self.next() & 0x7FFFFFFF) / 0x7FFFFFFF

    def next_range(self, lo: float, hi: float) -> float:
        return lo + self.next_float() * (hi - lo)


# ---------------------------------------------------------------------------
# Physics primitives
# ---------------------------------------------------------------------------


@dataclass
class Vec2:
    x: float = 0.0
    y: float = 0.0

    def __add__(self, o: Vec2) -> Vec2:
        return Vec2(self.x + o.x, self.y + o.y)

    def __sub__(self, o: Vec2) -> Vec2:
        return Vec2(self.x - o.x, self.y - o.y)

    def __mul__(self, s: float) -> Vec2:
        return Vec2(self.x * s, self.y * s)

    def __truediv__(self, s: float) -> Vec2:
        return Vec2(self.x / s, self.y / s)

    def __neg__(self) -> Vec2:
        return Vec2(-self.x, -self.y)

    def len(self) -> float:
        return math.hypot(self.x, self.y)

    def dot(self, o: Vec2) -> float:
        return self.x * o.x + self.y * o.y

    def normalize(self) -> Vec2:
        ln = self.len()
        if ln < 1e-9:
            return Vec2()
        return self / ln

    def rotated(self, angle: float) -> Vec2:
        c = math.cos(angle)
        s = math.sin(angle)
        return Vec2(self.x * c - self.y * s, self.x * s + self.y * c)

    def tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def ituple(self) -> Tuple[int, int]:
        return (int(round(self.x)), int(round(self.y)))


@dataclass
class Ball:
    pos: Vec2
    vel: Vec2
    alive: bool = True
    spawn_tick: int = 0


@dataclass
class Peg:
    pos: Vec2
    hit_count: int = 0
    id: int = 0


# ---------------------------------------------------------------------------
# SQLite persistence
# ---------------------------------------------------------------------------

DB_PATH = "pegfall.db"


def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS layouts ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  name TEXT NOT NULL,"
        "  seed INTEGER NOT NULL,"
        "  created_at TEXT NOT NULL DEFAULT (datetime('now')),"
        "  pegs_json TEXT NOT NULL"
        ")"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS runs ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  layout_id INTEGER,"
        "  seed INTEGER NOT NULL,"
        "  ticks INTEGER NOT NULL,"
        "  total_hits INTEGER NOT NULL,"
        "  histogram_json TEXT NOT NULL,"
        "  created_at TEXT NOT NULL DEFAULT (datetime('now')),"
        "  FOREIGN KEY(layout_id) REFERENCES layouts(id)"
        ")"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS settings ("
        "  key TEXT PRIMARY KEY,"
        "  value TEXT NOT NULL"
        ")"
    )
    conn.commit()
    return conn


def save_layout(conn: sqlite3.Connection, name: str, seed: int, pegs: List[Peg]) -> int:
    data = [{"x": p.pos.x, "y": p.pos.y, "hit_count": p.hit_count} for p in pegs]
    cur = conn.execute(
        "INSERT INTO layouts (name, seed, pegs_json) VALUES (?, ?, ?)",
        (name, seed, json.dumps(data)),
    )
    conn.commit()
    return cur.lastrowid


def load_latest_layout(conn: sqlite3.Connection) -> Optional[Tuple[int, int, List[Peg]]]:
    row = conn.execute(
        "SELECT id, seed, pegs_json FROM layouts ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return None
    lid, seed, pjson = row
    pegs = []
    for i, d in enumerate(json.loads(pjson)):
        pegs.append(Peg(pos=Vec2(d["x"], d["y"]), hit_count=d.get("hit_count", 0), id=i))
    return (lid, seed, pegs)


def save_run(
    conn: sqlite3.Connection, layout_id: int, seed: int, ticks: int,
    total_hits: int, histogram: List[int],
):
    conn.execute(
        "INSERT INTO runs (layout_id, seed, ticks, total_hits, histogram_json) VALUES (?, ?, ?, ?, ?)",
        (layout_id, seed, ticks, total_hits, json.dumps(histogram)),
    )
    conn.commit()


def load_setting(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row[0] if row else default


def save_setting(conn: sqlite3.Connection, key: str, value: str):
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------


class GameState:
    def __init__(self, seed: int, headless: bool = False):
        self.seed = seed
        self.rng = SeededRNG(seed)
        self.headless = headless

        self.pegs: List[Peg] = []
        self.balls: List[Ball] = []
        self.peg_counter = 0

        self.gravity_mode = 0  # 0=down, 1=up, 2=zero-g
        self.gravity_labels = ["Down", "Up", "Zero-G"]
        self.gravity_vecs = [Vec2(0, 980), Vec2(0, -980), Vec2(0, 0)]

        self.paused = False
        self.show_labels = False
        self.total_hits = 0
        self.tick_count = 0
        self.ball_spawn_counter = 0

        self.layout_id: Optional[int] = None  # last saved/loaded layout id

        self.red_flash_timer = 0.0
        self.toast_text = ""
        self.toast_timer = 0.0

        # For headless: store last positions checksum
        self._checksum_seed = seed

    @property
    def gravity(self) -> Vec2:
        return self.gravity_vecs[self.gravity_mode]

    def cycle_gravity(self):
        self.gravity_mode = (self.gravity_mode + 1) % 3

    def spawn_peg(self, pos: Vec2) -> bool:
        if len(self.pegs) >= MAX_PEGS:
            return False
        # Check overlap with existing pegs
        for p in self.pegs:
            if (p.pos - pos).len() < PEG_RADIUS * 2 + 2:
                self.red_flash_timer = RED_FLASH_DURATION
                return False
        peg = Peg(pos=pos, hit_count=0, id=self.peg_counter)
        self.peg_counter += 1
        self.pegs.append(peg)
        return True

    def delete_peg_at(self, pos: Vec2) -> bool:
        for i, p in enumerate(self.pegs):
            if (p.pos - pos).len() < PEG_RADIUS + 5:
                self.pegs.pop(i)
                return True
        return False

    def spawn_ball(self, pos: Vec2, vel: Vec2 = None):
        if len(self.balls) >= MAX_BALLS:
            self.balls.pop(0)  # oldest despawns
        b = Ball(pos=pos, vel=vel or Vec2(), alive=True, spawn_tick=self.tick_count)
        self.balls.append(b)
        self.ball_spawn_counter += 1

    def spawn_ball_chute(self):
        jitter_x = self.rng.next_range(-SPAWN_JITTER_PX, SPAWN_JITTER_PX)
        pos = Vec2(BOARD_W / 2 + jitter_x, 30)
        self.spawn_ball(pos)

    def spawn_ball_drag(self, start: Vec2, end: Vec2):
        vel = (end - start) * 2.0
        self.spawn_ball(start, vel)

    def clear_balls(self):
        self.balls.clear()

    def reset_counters(self):
        for p in self.pegs:
            p.hit_count = 0
        self.total_hits = 0

    def reseed(self):
        self.seed = random.randint(0, 2**31 - 1)
        self.rng = SeededRNG(self.seed)

    def physics_tick(self):
        if self.paused:
            return
        self.tick_count += 1
        g = self.gravity

        # Integrate balls
        for b in self.balls:
            if not b.alive:
                continue
            b.vel = b.vel + g * DT
            b.pos = b.pos + b.vel * DT

            # Zero-G speed clamp
            if self.gravity_mode == 2:
                spd = b.vel.len()
                if spd > MAX_SPEED_ZEROG:
                    b.vel = b.vel.normalize() * MAX_SPEED_ZEROG

            # Wall collisions
            self._wall_collide(b)

        # Ball-ball collisions
        for i in range(len(self.balls)):
            for j in range(i + 1, len(self.balls)):
                self._ball_ball_collide(self.balls[i], self.balls[j])

        # Ball-peg collisions
        for b in self.balls:
            if not b.alive:
                continue
            for p in self.pegs:
                self._ball_peg_collide(b, p)

        # Remove balls that have gone too far out of bounds
        self.balls = [
            b for b in self.balls
            if b.alive and -200 < b.pos.x < BOARD_W + 200 and -200 < b.pos.y < BOARD_H + 200
        ]

    def _wall_collide(self, b: Ball):
        r = BALL_RADIUS
        # Left wall
        if b.pos.x - r < 0:
            b.pos.x = r
            b.vel.x = -b.vel.x * WALL_RESTITUTION
        # Right wall
        if b.pos.x + r > BOARD_W:
            b.pos.x = BOARD_W - r
            b.vel.x = -b.vel.x * WALL_RESTITUTION
        # Top wall
        if b.pos.y - r < 0:
            b.pos.y = r
            b.vel.y = -b.vel.y * WALL_RESTITUTION
        # Bottom wall
        if b.pos.y + r > BOARD_H:
            b.pos.y = BOARD_H - r
            b.vel.y = -b.vel.y * WALL_RESTITUTION

    def _ball_ball_collide(self, a: Ball, b: Ball):
        if not a.alive or not b.alive:
            return
        delta = b.pos - a.pos
        dist = delta.len()
        min_d = BALL_RADIUS * 2
        if dist >= min_d or dist < 1e-9:
            return
        # Separate
        overlap = min_d - dist
        n = delta / dist
        a.pos = a.pos - n * (overlap / 2)
        b.pos = b.pos + n * (overlap / 2)
        # Relative velocity along normal
        rel_v = a.vel - b.vel
        vn = rel_v.dot(n)
        if vn > 0:
            return  # moving apart
        impulse = -vn * BALL_RESTITUTION
        a.vel = a.vel + n * impulse
        b.vel = b.vel - n * impulse

    def _ball_peg_collide(self, b: Ball, p: Peg):
        if not b.alive:
            return
        delta = b.pos - p.pos
        dist = delta.len()
        min_d = BALL_RADIUS + PEG_RADIUS
        if dist >= min_d or dist < 1e-9:
            return
        # Separate
        overlap = min_d - dist
        n = delta / dist
        b.pos = b.pos + n * overlap
        # Reflect velocity
        vn = b.vel.dot(n)
        if vn >= 0:
            return
        b.vel = b.vel - n * (1 + PEG_RESTITUTION) * vn
        # Record hit
        p.hit_count += 1
        self.total_hits += 1

    def get_hot_peg(self) -> Optional[Tuple[int, float]]:
        if not self.pegs or self.total_hits == 0:
            return None
        best = max(self.pegs, key=lambda p: p.hit_count)
        return (best.id, best.hit_count / self.total_hits * 100)

    def get_histogram(self) -> List[int]:
        return [p.hit_count for p in self.pegs]

    def positions_checksum(self) -> str:
        h = hashlib.md5()
        for b in self.balls:
            h.update(struct.pack("ff", b.pos.x, b.pos.y))
        return h.hexdigest()[:12]

    def run_headless(self, ticks: int) -> dict:
        """Run simulation with no rendering for given ticks. Return summary."""
        for _ in range(ticks):
            self.physics_tick()
        hot = self.get_hot_peg()
        return {
            "seed": self.seed,
            "ticks": self.tick_count,
            "total_hits": self.total_hits,
            "hot_peg_id": hot[0] if hot else -1,
            "hot_peg_pct": round(hot[1], 1) if hot else 0.0,
            "alive_balls": len(self.balls),
            "checksum": self.positions_checksum(),
            "histogram": self.get_histogram(),
        }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def draw_board(screen, state: GameState, font, font_small):
    screen.fill(BG_COLOR)

    # Draw walls (border)
    pygame.draw.rect(screen, WALL_COLOR, (0, 0, BOARD_W, BOARD_H), 2)

    # Draw pegs
    for p in state.pegs:
        color = _peg_color(p, state.total_hits)
        px, py = p.pos.ituple()
        pygame.draw.circle(screen, color, (px, py), PEG_RADIUS)
        if p.hit_count > 0:
            # Heat glow
            glow = _peg_color(p, state.total_hits, alpha=True)
            pygame.draw.circle(screen, glow, (px, py), PEG_RADIUS + 3, 2)

        if state.show_labels:
            label = font_small.render(str(p.hit_count), True, (255, 255, 200))
            screen.blit(label, (px - 10, py - 6))

    # Draw balls
    for b in state.balls:
        px, py = b.pos.ituple()
        pygame.draw.circle(screen, BALL_COLOR, (px, py), BALL_RADIUS)
        pygame.draw.circle(screen, (255, 255, 200), (px, py), BALL_RADIUS, 1)

    # Red flash overlay
    if state.red_flash_timer > 0:
        surf = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        surf.fill((255, 0, 0, 60))
        screen.blit(surf, (0, 0))

    # HUD
    hud_lines = [
        f"Seed: {state.seed}  |  Grav: {state.gravity_labels[state.gravity_mode]}",
        f"Balls: {len(state.balls)}/{MAX_BALLS}  |  Pegs: {len(state.pegs)}/{MAX_PEGS}  |  Hits: {state.total_hits}",
    ]
    hot = state.get_hot_peg()
    if hot:
        hud_lines.append(f"Hot peg #{hot[0]}: {hot[1]:.1f}%")
    else:
        hud_lines.append("Hot peg: --")

    if state.paused:
        hud_lines.append(">>> PAUSED <<<")

    hud_lines.append("[B]all  [G]rav  [N]reseed  [C]lear  [0]reset  Space=pause  [Tab]labels")

    y = BOARD_H + 4
    for line in hud_lines:
        surf = font.render(line, True, HUD_COLOR)
        screen.blit(surf, (8, y))
        y += 18

    # Toast
    if state.toast_timer > 0:
        ts = font.render(state.toast_text, True, (100, 255, 100))
        screen.blit(ts, (BOARD_W // 2 - ts.get_width() // 2, BOARD_H // 2 - 20))


def _peg_color(p: Peg, total_hits: int, alpha: bool = False) -> Tuple[int, ...]:
    if total_hits == 0 or p.hit_count == 0:
        base = PEG_COLOR
    else:
        t = min(p.hit_count / max(total_hits, 1) * 5, 1.0)
        base = (
            int(PEG_HOT_MIN[0] + (PEG_HOT_MAX[0] - PEG_HOT_MIN[0]) * t),
            int(PEG_HOT_MIN[1] + (PEG_HOT_MAX[1] - PEG_HOT_MIN[1]) * t),
            int(PEG_HOT_MIN[2] + (PEG_HOT_MAX[2] - PEG_HOT_MIN[2]) * t),
        )
    if alpha:
        return base + (120,)
    return base


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def main_loop(state: GameState, conn: sqlite3.Connection):
    pygame.init()
    screen = pygame.display.set_mode((BOARD_W, BOARD_H + 80))
    pygame.display.set_caption("Pegfall Lab")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Consolas", 14)
    font_small = pygame.font.SysFont("Consolas", 11)

    running = True
    drag_start: Optional[Vec2] = None
    acc = 0.0

    # Restore settings
    grav_val = load_setting(conn, "gravity_mode", "0")
    try:
        state.gravity_mode = int(grav_val) % 3
    except ValueError:
        state.gravity_mode = 0
    lbl_val = load_setting(conn, "show_labels", "0")
    state.show_labels = lbl_val == "1"

    def toast(msg: str, dur: float = 2.0):
        state.toast_text = msg
        state.toast_timer = dur

    while running:
        dt_real = clock.tick(FPS) / 1000.0
        if state.red_flash_timer > 0:
            state.red_flash_timer -= dt_real
        if state.toast_timer > 0:
            state.toast_timer -= dt_real

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Autosave
                if state.pegs:
                    save_layout(conn, "autosave", state.seed, state.pegs)
                save_setting(conn, "gravity_mode", str(state.gravity_mode))
                save_setting(conn, "show_labels", "1" if state.show_labels else "0")
                running = False
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    continue

                elif event.key == pygame.K_b:
                    state.spawn_ball_chute()
                    toast("Ball dropped!")

                elif event.key == pygame.K_g:
                    state.cycle_gravity()
                    toast(f"Gravity: {state.gravity_labels[state.gravity_mode]}")

                elif event.key == pygame.K_n:
                    state.reseed()
                    toast(f"Reseeded: {state.seed}")

                elif event.key == pygame.K_SPACE:
                    state.paused = not state.paused

                elif event.key == pygame.K_c:
                    state.clear_balls()
                    toast("Balls cleared")

                elif event.key == pygame.K_0:
                    state.reset_counters()
                    toast("Counters reset")

                elif event.key == pygame.K_TAB:
                    state.show_labels = not state.show_labels

                elif event.key == pygame.K_F5:
                    if state.pegs:
                        lid = save_layout(conn, "manual", state.seed, state.pegs)
                        state.layout_id = lid
                        toast("Layout saved!")
                    else:
                        toast("No pegs to save", 1.0)

                elif event.key == pygame.K_F9:
                    loaded = load_latest_layout(conn)
                    if loaded:
                        lid, seed, pegs = loaded
                        state.pegs = pegs
                        state.seed = seed
                        state.rng = SeededRNG(seed)
                        state.layout_id = lid
                        state.peg_counter = max((p.id for p in pegs), default=0) + 1
                        state.total_hits = sum(p.hit_count for p in pegs)
                        toast(f"Layout loaded ({len(pegs)} pegs)")
                    else:
                        toast("No saved layout", 1.0)

                elif event.key == pygame.K_r:
                    if state.balls:
                        toast("Recording run...")
                        histogram = state.get_histogram()
                        save_run(
                            conn, state.layout_id or 0, state.seed,
                            state.tick_count, state.total_hits, histogram,
                        )
                        # Reset for next run
                        state.clear_balls()
                        state.reset_counters()
                        toast("Run recorded!")
                    else:
                        toast("No balls to record", 1.0)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = Vec2(event.pos[0], event.pos[1])
                if pos.y > BOARD_H:
                    continue
                if event.button == 1:  # Left click
                    # Check if clicking on existing peg (select / drag potential)
                    hit_peg = False
                    for p in state.pegs:
                        if (p.pos - pos).len() < PEG_RADIUS + 5:
                            hit_peg = True
                            break
                    if not hit_peg:
                        drag_start = pos
                elif event.button == 3:  # Right click
                    state.delete_peg_at(pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and drag_start is not None:
                    end = Vec2(event.pos[0], event.pos[1])
                    if end.y > BOARD_H:
                        drag_start = None
                        continue
                    dist = (end - drag_start).len()
                    if dist < 8:
                        # Place peg
                        state.spawn_peg(drag_start)
                    else:
                        # Drag-spawn ball
                        state.spawn_ball_drag(drag_start, end)
                        toast("Ball launched!")
                    drag_start = None

        # Physics
        acc += dt_real
        while acc >= DT:
            state.physics_tick()
            acc -= DT

        # Cap accumulator
        if acc > 0.1:
            acc = 0.1

        # Render
        draw_board(screen, state, font, font_small)

        if drag_start is not None:
            mx, my = pygame.mouse.get_pos()
            pygame.draw.line(screen, (200, 200, 100), drag_start.ituple(), (mx, my), 1)

        pygame.display.flip()

    pygame.quit()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Pegfall Lab — physics sandbox")
    parser.add_argument("--headless", action="store_true", help="Run headless smoke mode")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed")
    parser.add_argument("--ticks", type=int, default=600, help="Physics ticks for headless mode")
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else random.randint(0, 2**31 - 1)

    state = GameState(seed=seed, headless=args.headless)

    if args.headless:
        # Add some default pegs for headless mode
        import random as std_random
        rng_local = std_random.Random(seed)
        attempts = 0
        while len(state.pegs) < 20 and attempts < 200:
            attempts += 1
            px = rng_local.uniform(PEG_RADIUS + 10, BOARD_W - PEG_RADIUS - 10)
            py = rng_local.uniform(PEG_RADIUS + 50, BOARD_H - PEG_RADIUS - 10)
            state.spawn_peg(Vec2(px, py))

        # Drop some balls
        for _ in range(5):
            state.spawn_ball_chute()

        summary = state.run_headless(args.ticks)
        print("--- Headless Summary ---")
        for k, v in summary.items():
            print(f"  {k}: {v}")
        print("------------------------")
        return

    conn = init_db()
    try:
        main_loop(state, conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
