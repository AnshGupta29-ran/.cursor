"""Core Tap game engine — pure logic, no pygame import.

Invariants (tested):
  * Pulse speed never exceeds SPEED_CAP.
  * Swept (sub-stepped) collision: a pulse at max speed can never tunnel
    through a brick — sub-step length <= PULSE_RADIUS.
  * Timed modules stack by REFRESH (timer reset), never duration-add.
  * Reflection angle is linear in impact offset, clamped to
    +/- MAX_BOUNCE_ANGLE off vertical.
  * Drops use the run's seeded RNG; RNG state is part of the snapshot.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from .constants import (
    ALL_MODULES, BRICK_SPECS, COL_MODULE, DEPTH_MULTIPLIERS, DRAG_FIELD_FACTOR,
    DRAG_FIELD_SECONDS, LAUNCH_SPEED, M_DRAG, M_PIERCE, M_SPARE, M_SPLIT,
    M_WIDE, MAX_BOUNCE_ANGLE, MAX_PULSES, MODULE_DROP_RATES, MODULE_FALL_SPEED,
    MODULE_HEIGHT, MODULE_WIDTH, PIERCE_SECONDS, PULSE_RADIUS, RIG_HEIGHT,
    RIG_SPEED, RIG_WIDTH, RIG_Y, SPEEDUP_PER_BRICK, SPEED_CAP, START_HULLS,
    HEIGHT, WIDTH, WIDE_RIG_FACTOR,
)
from .level import Site, brick_geometry


@dataclass
class Pulse:
    x: float
    y: float
    vx: float
    vy: float
    attached: bool = False

    @property
    def speed(self) -> float:
        return math.hypot(self.vx, self.vy)


@dataclass
class Brick:
    cls: str
    x: float
    y: float
    w: float
    h: float
    hits_left: int

    @property
    def destructible(self) -> bool:
        return BRICK_SPECS[self.cls]["hits"] is not None


@dataclass
class ModuleDrop:
    kind: str
    x: float
    y: float


@dataclass
class Event:
    kind: str          # "brick", "lost", "clear", "gameover", "module"
    data: dict = field(default_factory=dict)


class Game:
    """A full run: chain of sites, score, hulls, pulses, modules, RNG."""

    def __init__(self, sites: list[Site], seed: int = 0):
        if not sites:
            raise ValueError("need at least one site")
        self.sites = sites
        self.seed = seed
        self.rng = random.Random(seed)
        self.site_index = 0
        self.score = 0
        self.hulls = START_HULLS
        self.pulses: list[Pulse] = []
        self.bricks: list[Brick] = []
        self.drops: list[ModuleDrop] = []
        self.timers: dict[str, float] = {}   # kind -> seconds remaining
        self.wide = False
        self.rig_x = WIDTH / 2
        self.speed_bonus = 0.0
        self.state = "playing"               # playing | siteclear | gameover | win
        self._load_site(0)

    # ----- site / brick setup -------------------------------------------------
    def _load_site(self, idx: int) -> None:
        site = self.sites[idx]
        self.bricks = []
        for c, r, x, y, w, h in brick_geometry(site):
            cls = site.grid[r][c]
            hits = BRICK_SPECS[cls]["hits"] or 0
            self.bricks.append(Brick(cls=cls, x=x, y=y, w=w, h=h, hits_left=hits))
        self.drops = []
        self.speed_bonus = 0.0
        self._respawn()

    def _respawn(self) -> None:
        self.pulses = [Pulse(self.rig_x, RIG_Y - PULSE_RADIUS - 1, 0.0, 0.0,
                             attached=True)]

    @property
    def site(self) -> Site:
        return self.sites[self.site_index]

    @property
    def depth_multiplier(self) -> float:
        i = min(self.site_index, len(DEPTH_MULTIPLIERS) - 1)
        return DEPTH_MULTIPLIERS[i]

    @property
    def rig_width(self) -> float:
        return RIG_WIDTH * (WIDE_RIG_FACTOR if self.wide else 1.0)

    def base_speed(self) -> float:
        s = (LAUNCH_SPEED + self.speed_bonus) * self.site.speed_ramp
        if M_DRAG in self.timers:
            s *= DRAG_FIELD_FACTOR
        return min(s, SPEED_CAP)

    # ----- input --------------------------------------------------------------
    def move_rig(self, direction: float, dt: float) -> None:
        """direction in [-1, 1]; rig speed clamped; rig clamped to window."""
        self.rig_x += max(-1.0, min(1.0, direction)) * RIG_SPEED * dt
        half = self.rig_width / 2
        self.rig_x = max(half, min(WIDTH - half, self.rig_x))

    def launch(self) -> None:
        for p in self.pulses:
            if p.attached:
                p.attached = False
                ang = self.rng.uniform(-0.35, 0.35)
                s = self.base_speed()
                p.vx = s * math.sin(ang)
                p.vy = -s * math.cos(ang)

    # ----- modules ------------------------------------------------------------
    def apply_module(self, kind: str) -> None:
        if kind == M_WIDE:
            self.wide = True
        elif kind == M_SPARE:
            self.hulls += 1
        elif kind == M_SPLIT:
            self._split_pulses()
        elif kind == M_DRAG:
            self._refresh(M_DRAG, DRAG_FIELD_SECONDS)
        elif kind == M_PIERCE:
            self._refresh(M_PIERCE, PIERCE_SECONDS)

    def _refresh(self, kind: str, seconds: float) -> None:
        # REFRESH-stacking invariant: never duration-add.
        self.timers[kind] = seconds

    def _split_pulses(self) -> None:
        room = MAX_PULSES - len(self.pulses)
        if room <= 0:
            return
        new: list[Pulse] = []
        for p in list(self.pulses):
            if len(new) >= room:
                break
            if p.attached:
                continue
            ang = math.atan2(p.vx, -p.vy)
            s = max(p.speed, 1.0)
            a2 = ang + math.radians(25)
            new.append(Pulse(p.x, p.y, s * math.sin(a2), -s * math.cos(a2)))
        self.pulses.extend(new[:room])

    # ----- update -------------------------------------------------------------
    def tick(self, dt: float) -> list[Event]:
        """Advance the simulation by dt seconds. Returns events."""
        events: list[Event] = []
        if self.state != "playing":
            return events
        # timers
        for kind in list(self.timers):
            self.timers[kind] -= dt
            if self.timers[kind] <= 0:
                del self.timers[kind]
        # pulses
        speed = self.base_speed()
        for p in self.pulses:
            if p.attached:
                p.x, p.y = self.rig_x, RIG_Y - PULSE_RADIUS - 1
                continue
            self._sweep(p, dt, events)
            self._clamp_speed(p, speed)
        # lost pulses
        lost = [p for p in self.pulses if p.y - PULSE_RADIUS > HEIGHT]
        if lost:
            self.pulses = [p for p in self.pulses if p not in lost]
            if not self.pulses:
                self.hulls -= 1
                events.append(Event("lost", {"hulls": self.hulls}))
                if self.hulls <= 0:
                    self.state = "gameover"
                    events.append(Event("gameover"))
                else:
                    self._respawn()
        # falling module drops
        rig_top = RIG_Y
        for d in list(self.drops):
            d.y += MODULE_FALL_SPEED * dt
            if (rig_top - 4 <= d.y <= rig_top + RIG_HEIGHT + 10
                    and abs(d.x - self.rig_x) <= self.rig_width / 2 + MODULE_WIDTH / 2):
                self.apply_module(d.kind)
                events.append(Event("module", {"kind": d.kind}))
                self.drops.remove(d)
            elif d.y > HEIGHT + 20:
                self.drops.remove(d)
        # site clear
        if self.state == "playing" and not any(b.destructible for b in self.bricks):
            if self.site_index + 1 < len(self.sites):
                self.state = "siteclear"
                events.append(Event("clear", {"site": self.site_index}))
            else:
                self.state = "win"
                events.append(Event("win"))
        return events

    def advance_site(self) -> None:
        if self.state == "siteclear":
            self.site_index += 1
            self.state = "playing"
            self._load_site(self.site_index)

    def _clamp_speed(self, p: Pulse, target: float) -> None:
        s = p.speed
        if s < 1e-6:
            p.vy = -target
            return
        if abs(s - target) > 1e-6:
            p.vx *= target / s
            p.vy *= target / s
        # hard cap invariant
        if p.speed > SPEED_CAP:
            f = SPEED_CAP / p.speed
            p.vx *= f
            p.vy *= f

    # ----- swept collision ----------------------------------------------------
    def _sweep(self, p: Pulse, dt: float, events: list[Event]) -> None:
        dist = p.speed * dt
        steps = max(1, math.ceil(dist / PULSE_RADIUS))
        sub = dt / steps
        for _ in range(steps):
            p.x += p.vx * sub
            p.y += p.vy * sub
            self._walls(p)
            self._rig_bounce(p)
            self._brick_hits(p, events)

    def _walls(self, p: Pulse) -> None:
        if p.x - PULSE_RADIUS < 0:
            p.x = PULSE_RADIUS
            p.vx = abs(p.vx)
        elif p.x + PULSE_RADIUS > WIDTH:
            p.x = WIDTH - PULSE_RADIUS
            p.vx = -abs(p.vx)
        if p.y - PULSE_RADIUS < 0:
            p.y = PULSE_RADIUS
            p.vy = abs(p.vy)

    def _rig_bounce(self, p: Pulse) -> None:
        if p.vy <= 0:
            return
        half = self.rig_width / 2
        if (RIG_Y - PULSE_RADIUS <= p.y <= RIG_Y + RIG_HEIGHT
                and abs(p.x - self.rig_x) <= half + PULSE_RADIUS):
            offset = max(-1.0, min(1.0, (p.x - self.rig_x) / half))
            ang = math.radians(MAX_BOUNCE_ANGLE) * offset
            s = max(p.speed, 1.0)
            p.vx = s * math.sin(ang)
            p.vy = -abs(s * math.cos(ang))
            p.y = RIG_Y - PULSE_RADIUS

    def _brick_hits(self, p: Pulse, events: list[Event]) -> None:
        pierce = M_PIERCE in self.timers
        for b in list(self.bricks):
            if not self._overlap(p, b):
                continue
            if b.destructible:
                b.hits_left -= 1
                if b.hits_left <= 0:
                    self._fracture(b, events)
                else:
                    events.append(Event("brick", {"cls": b.cls, "cracked": True}))
            if pierce:
                continue
            self._reflect(p, b)
            return  # one reflection per sub-step

    @staticmethod
    def _overlap(p: Pulse, b: Brick) -> bool:
        cx = max(b.x, min(p.x, b.x + b.w))
        cy = max(b.y, min(p.y, b.y + b.h))
        return (p.x - cx) ** 2 + (p.y - cy) ** 2 <= PULSE_RADIUS ** 2

    @staticmethod
    def _reflect(p: Pulse, b: Brick) -> None:
        # reflect along the axis of least penetration
        dx_left = (p.x + PULSE_RADIUS) - b.x
        dx_right = (b.x + b.w) - (p.x - PULSE_RADIUS)
        dy_top = (p.y + PULSE_RADIUS) - b.y
        dy_bot = (b.y + b.h) - (p.y - PULSE_RADIUS)
        m = min(dx_left, dx_right, dy_top, dy_bot)
        if m in (dx_left, dx_right):
            p.vx = -p.vx
            p.x += 1 if dx_left < dx_right else -1
        else:
            p.vy = -p.vy
            p.y += 1 if dy_top < dy_bot else -1

    def _fracture(self, b: Brick, events: list[Event]) -> None:
        self.bricks.remove(b)
        spec = BRICK_SPECS[b.cls]
        pts = int(spec["points"] * self.depth_multiplier)
        self.score += pts
        self.speed_bonus += SPEEDUP_PER_BRICK
        events.append(Event("brick", {"cls": b.cls, "points": pts}))
        rate = MODULE_DROP_RATES["ore" if b.cls == "ore" else "other"]
        if self.rng.random() < rate:
            kind = self.rng.choice(ALL_MODULES)
            self.drops.append(ModuleDrop(kind, b.x + b.w / 2, b.y + b.h / 2))

    # ----- snapshot codec -----------------------------------------------------
    def export_snapshot(self) -> dict:
        from .snapshot import encode_rng
        return {
            "version": 1,
            "game": "coretap",
            "site_index": self.site_index,
            "score": self.score,
            "hulls": self.hulls,
            "seed": self.seed,
            "rng_state": encode_rng(self.rng),
            "state": self.state,
            "speed_bonus": self.speed_bonus,
            "rig_x": self.rig_x,
            "wide": self.wide,
            "timers": dict(self.timers),
            "brick_bitmap": self._bitmap(),
            "pulses": [
                {"x": p.x, "y": p.y, "vx": p.vx, "vy": p.vy, "attached": p.attached}
                for p in self.pulses
            ],
            "drops": [{"kind": d.kind, "x": d.x, "y": d.y} for d in self.drops],
        }

    def _bitmap(self) -> list[dict]:
        """Bitmap ordered by grid scan (row-major); dead cells are None."""
        alive: dict[tuple[int, int], Brick] = {}
        # reconstruct positions from geometry
        for c, r, x, y, w, h in brick_geometry(self.site):
            for b in self.bricks:
                if abs(b.x - x) < 0.5 and abs(b.y - y) < 0.5:
                    alive[(r, c)] = b
                    break
        out = []
        for r, row in enumerate(self.site.grid):
            for c, cls in enumerate(row):
                if not cls:
                    continue
                b = alive.get((r, c))
                out.append({"cls": cls, "hits": b.hits_left if b else 0})
        return out

    @classmethod
    def import_snapshot(cls, sites: list[Site], snap: dict) -> "Game":
        from .snapshot import decode_rng, validate_snapshot
        validate_snapshot(snap)
        g = cls(sites, seed=snap["seed"])
        g.site_index = snap["site_index"]
        g.score = snap["score"]
        g.hulls = snap["hulls"]
        g.rng = decode_rng(snap["rng_state"])
        g.state = snap["state"]
        g.rig_x = snap["rig_x"]
        g.wide = snap["wide"]
        g.timers = dict(snap["timers"])
        g._load_site(g.site_index)
        g.speed_bonus = snap["speed_bonus"]  # after _load_site: it resets it
        # apply brick bitmap (row-major over non-empty cells)
        cells = [(r, c) for r, row in enumerate(g.site.grid)
                 for c, cls in enumerate(row) if cls]
        bm = snap["brick_bitmap"]
        if len(bm) != len(cells):
            from .snapshot import SnapshotError
            raise SnapshotError(
                f"brick_bitmap has {len(bm)} cells, site needs {len(cells)}")
        geom = {(r, c): (x, y, w, h) for c, r, x, y, w, h in brick_geometry(g.site)}
        g.bricks = []
        for (r, c), cell in zip(cells, bm):
            if cell["hits"] <= 0:
                continue
            x, y, w, h = geom[(r, c)]
            g.bricks.append(Brick(cls=cell["cls"], x=x, y=y, w=w, h=h,
                                  hits_left=cell["hits"]))
        g.pulses = [Pulse(p["x"], p["y"], p["vx"], p["vy"], p["attached"])
                    for p in snap["pulses"]]
        g.drops = [ModuleDrop(d["kind"], d["x"], d["y"]) for d in snap["drops"]]
        return g
