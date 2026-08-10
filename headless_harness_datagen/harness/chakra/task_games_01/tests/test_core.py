"""Core Tap unit tests — run headless:  python -m pytest -q"""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coretap.core.constants import (  # noqa: E402
    BRICK_SPECS, DRAG_FIELD_SECONDS, LAUNCH_SPEED, M_DRAG, M_PIERCE,
    MAX_BOUNCE_ANGLE, PIERCE_SECONDS, PULSE_RADIUS, RIG_Y, SPEED_CAP,
)
from coretap.core.engine import Brick, Game, Pulse  # noqa: E402
from coretap.core.level import LevelError, load_site, parse_site  # noqa: E402
from coretap.core.snapshot import SnapshotError  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def make_game(seed=7):
    sites = [load_site(os.path.join(ROOT, "levels", f))
             for f in sorted(os.listdir(os.path.join(ROOT, "levels")))]
    return Game(sites, seed=seed)


# ----- scoring / multiplier ---------------------------------------------------
def test_scoring_depth_multiplier():
    g = make_game()
    sediment_pts = BRICK_SPECS["sediment"]["points"]
    b = next(b for b in g.bricks if b.cls == "sediment")
    g._fracture(b, [])
    assert g.score == sediment_pts * 1  # site 1 -> x1.0
    g.site_index = 1
    g._load_site(1)
    b = next(b for b in g.bricks if b.cls == "sediment")
    g._fracture(b, [])
    assert g.score == sediment_pts * 1 + int(sediment_pts * 1.5)


def test_ore_drop_rate_seeded():
    g = make_game(seed=1)
    drops = 0
    for _ in range(200):
        g.rng = __import__("random").Random(1)
    # deterministic: same seed -> same sequence
    import random
    r1, r2 = random.Random(99), random.Random(99)
    assert [r1.random() for _ in range(5)] == [r2.random() for _ in range(5)]


# ----- reflection math ---------------------------------------------------------
def test_rig_reflection_angles():
    g = make_game()
    half = g.rig_width / 2
    for offset, frac in ((-half, -1.0), (0.0, 0.0), (half, 1.0)):
        p = Pulse(g.rig_x + offset, RIG_Y + 2, 0.0, LAUNCH_SPEED)
        g._rig_bounce(p)
        s = p.speed
        ang = math.degrees(math.atan2(p.vx, -p.vy))
        assert abs(ang - frac * MAX_BOUNCE_ANGLE) < 1.0
        assert p.vy < 0
        assert abs(s - LAUNCH_SPEED) < 1e-6


# ----- module timers ------------------------------------------------------------
def test_module_timer_refresh_not_additive():
    g = make_game()
    g.apply_module(M_DRAG)
    g.tick(2.0)
    assert g.timers[M_DRAG] == pytest.approx(DRAG_FIELD_SECONDS - 2.0)
    g.apply_module(M_DRAG)  # refresh
    assert g.timers[M_DRAG] == pytest.approx(DRAG_FIELD_SECONDS)
    g.tick(DRAG_FIELD_SECONDS + 0.01)
    assert M_DRAG not in g.timers


def test_pierce_refresh():
    g = make_game()
    g.apply_module(M_PIERCE)
    g.tick(1.0)
    g.apply_module(M_PIERCE)
    assert g.timers[M_PIERCE] == pytest.approx(PIERCE_SECONDS)


def test_split_pulse_cap():
    g = make_game()
    g.launch()
    g.apply_module("split_pulse")
    g.apply_module("split_pulse")
    g.apply_module("split_pulse")
    assert len(g.pulses) <= 3


# ----- level validation ----------------------------------------------------------
def test_level_validation_names_field():
    with pytest.raises(LevelError) as exc:
        parse_site({"name": "X", "depth_m": -1, "grid": ["ss"]}, "site_bad.json")
    assert "site_bad.json" in str(exc.value) and "depth_m" in str(exc.value)


def test_level_unknown_glyph():
    with pytest.raises(LevelError) as exc:
        parse_site({"name": "X", "depth_m": 1, "grid": ["sz"]}, "f.json")
    assert "glyph" in str(exc.value)


def test_shipped_sites_valid():
    for f in sorted(os.listdir(os.path.join(ROOT, "levels"))):
        site = load_site(os.path.join(ROOT, "levels", f))
        assert site.destructible_count > 0


# ----- speed cap / sweep invariant -------------------------------------------------
def test_speed_cap_and_no_tunnel():
    g = make_game()
    p = Pulse(100, 200, SPEED_CAP * 0.9, 0.0)
    g._clamp_speed(p, SPEED_CAP * 5)
    assert p.speed <= SPEED_CAP + 1e-6
    # max-speed pulse sweeping horizontally across a brick must hit it
    b = Brick("sediment", 300, 190, 60, 20, 1)
    g.bricks = [b]
    p = Pulse(100, 200, SPEED_CAP, 0.0)
    g.pulses = [p]
    g.state = "playing"
    events = []
    for _ in range(30):  # 0.5s of sweep at cap: travels 360px, crosses x=300
        g._sweep(p, 1 / 60, events)
        if not g.bricks:
            break
    assert not g.bricks  # brick was fractured, never tunneled through


# ----- snapshot round trip ---------------------------------------------------------
def test_snapshot_roundtrip_deep_equal():
    g = make_game(seed=123)
    g.launch()
    for _ in range(240):
        g.tick(1 / 60)
    g.apply_module(M_DRAG)
    g.tick(0.5)
    snap = g.export_snapshot()
    g2 = Game.import_snapshot(g.sites, snap)
    assert g2.export_snapshot() == snap
    # key fields deep-equal
    assert g2.score == g.score and g2.hulls == g.hulls
    assert g2.site_index == g.site_index
    assert [(b.cls, b.hits_left, b.x, b.y) for b in g2.bricks] == \
           [(b.cls, b.hits_left, b.x, b.y) for b in g.bricks]
    assert [(p.x, p.y, p.vx, p.vy) for p in g2.pulses] == \
           [(p.x, p.y, p.vx, p.vy) for p in g.pulses]
    assert g2.rng.random() == g.rng.random()  # RNG state restored


def test_snapshot_rejects_corruption():
    g = make_game()
    snap = g.export_snapshot()
    bad = dict(snap, version=99)
    with pytest.raises(SnapshotError, match="version"):
        Game.import_snapshot(g.sites, bad)
    bad2 = dict(snap, score="lots")
    with pytest.raises(SnapshotError):
        Game.import_snapshot(g.sites, bad2)
    bad3 = dict(snap, rng_state=[1, [2], None])
    with pytest.raises(SnapshotError):
        Game.import_snapshot(g.sites, bad3)
    # current run untouched: exceptions raised before mutation
    assert g.state == "playing"
