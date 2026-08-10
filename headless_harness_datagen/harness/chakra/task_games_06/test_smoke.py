#!/usr/bin/env python3
"""
Smoke tests for Pegfall Lab — collision sanity, spawn reject,
determinism, SQLite round-trip.
"""

import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import (
    GameState, Vec2, Ball, Peg,
    SeededRNG, BALL_RADIUS, PEG_RADIUS, MAX_PEGS, MAX_BALLS,
    init_db, save_layout, load_latest_layout, save_run, BOARD_W, BOARD_H,
)


def test_seeded_rng_deterministic():
    """Same seed produces same sequence."""
    a = SeededRNG(42)
    b = SeededRNG(42)
    for _ in range(100):
        assert a.next() == b.next(), "RNG mismatch"


def test_spawn_peg():
    state = GameState(seed=1)
    ok = state.spawn_peg(Vec2(100, 100))
    assert ok, "First peg should spawn"
    assert len(state.pegs) == 1


def test_spawn_peg_reject_overlap():
    state = GameState(seed=1)
    state.spawn_peg(Vec2(100, 100))
    # Too close
    ok = state.spawn_peg(Vec2(100 + PEG_RADIUS, 100))
    assert not ok, "Overlapping peg should be rejected"
    assert len(state.pegs) == 1


def test_spawn_peg_max():
    state = GameState(seed=1)
    for i in range(MAX_PEGS):
        ok = state.spawn_peg(Vec2(30 + i * 25, 100))
        assert ok, f"Peg {i} should spawn"
    assert len(state.pegs) == MAX_PEGS
    ok = state.spawn_peg(Vec2(400, 400))
    assert not ok, "Over max pegs should be rejected"


def test_delete_peg():
    state = GameState(seed=1)
    state.spawn_peg(Vec2(100, 100))
    assert state.delete_peg_at(Vec2(100, 100))
    assert len(state.pegs) == 0


def test_collision_counts():
    """Ball hitting peg increments counter."""
    state = GameState(seed=1)
    state.spawn_peg(Vec2(300, 300))
    b = Ball(pos=Vec2(290, 300), vel=Vec2(100, 0))
    state.balls.append(b)
    # Run enough ticks
    for _ in range(200):
        state.physics_tick()
    assert state.pegs[0].hit_count > 0, "Peg should have been hit"
    assert state.total_hits > 0


def test_determinism_same_seed():
    """Two runs with same seed produce identical histograms."""
    def run(seed):
        s = GameState(seed=seed)
        # Place identical pegs
        for px, py in [(100, 150), (200, 200), (300, 180), (400, 220), (500, 160)]:
            s.spawn_peg(Vec2(px, py))
        # Drop balls identically
        s.rng = SeededRNG(seed)  # reset RNG
        for _ in range(3):
            s.spawn_ball_chute()
        s.run_headless(300)
        return s.get_histogram(), s.total_hits, s.tick_count

    h1, th1, tc1 = run(777)
    h2, th2, tc2 = run(777)
    assert h1 == h2, f"Histograms differ: {h1} vs {h2}"
    assert th1 == th2, f"Total hits differ: {th1} vs {th2}"
    assert tc1 == tc2, f"Tick counts differ: {tc1} vs {tc2}"


def test_budget_limits():
    """Enforce 32 ball / 64 peg caps."""
    state = GameState(seed=1)
    for i in range(MAX_PEGS):
        state.spawn_peg(Vec2(30 + i * 25, 100))
    assert len(state.pegs) == MAX_PEGS
    state.spawn_peg(Vec2(500, 500))
    assert len(state.pegs) == MAX_PEGS

    for i in range(MAX_BALLS + 5):
        state.spawn_ball(Vec2(400, 50))
    assert len(state.balls) <= MAX_BALLS


def test_sqlite_round_trip():
    """Save layout then load it back."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    try:
        # Override DB_PATH
        import main as m
        orig_path = m.DB_PATH
        m.DB_PATH = db_path

        conn = init_db()
        state = GameState(seed=42)
        state.spawn_peg(Vec2(100, 100))
        state.spawn_peg(Vec2(200, 200))
        lid = save_layout(conn, "test", 42, state.pegs)
        assert lid is not None and lid > 0

        loaded = load_latest_layout(conn)
        assert loaded is not None
        lid2, seed2, pegs2 = loaded
        assert seed2 == 42
        assert len(pegs2) == 2
        assert abs(pegs2[0].pos.x - 100) < 1
        conn.close()

        m.DB_PATH = orig_path
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_gravity_cycle():
    state = GameState(seed=1)
    assert state.gravity_mode == 0
    state.cycle_gravity()
    assert state.gravity_mode == 1
    state.cycle_gravity()
    assert state.gravity_mode == 2
    state.cycle_gravity()
    assert state.gravity_mode == 0


def test_reseed():
    state = GameState(seed=100)
    old = state.seed
    state.reseed()
    assert state.seed != old


def test_headless_idempotent():
    """Running headless twice with same seed gives identical output."""
    def run_headless(seed):
        state = GameState(seed=seed)
        import random as std_random
        rng = std_random.Random(seed)
        for _ in range(15):
            px = rng.uniform(PEG_RADIUS + 10, BOARD_W - PEG_RADIUS - 10)
            py = rng.uniform(PEG_RADIUS + 50, BOARD_H - PEG_RADIUS - 10)
            state.spawn_peg(Vec2(px, py))
        for _ in range(3):
            state.spawn_ball_chute()
        return state.run_headless(300)

    r1 = run_headless(42)
    r2 = run_headless(42)
    assert r1["total_hits"] == r2["total_hits"]
    assert r1["histogram"] == r2["histogram"]
    assert r1["checksum"] == r2["checksum"]


def test_hot_peg():
    state = GameState(seed=1)
    state.spawn_peg(Vec2(100, 200))
    state.spawn_peg(Vec2(300, 200))
    # Simulate hits
    state.pegs[0].hit_count = 5
    state.pegs[1].hit_count = 3
    state.total_hits = 8
    hot = state.get_hot_peg()
    assert hot is not None
    assert hot[0] == 0
    assert abs(hot[1] - 62.5) < 1


if __name__ == "__main__":
    tests = [
        ("RNG determinism", test_seeded_rng_deterministic),
        ("Spawn peg", test_spawn_peg),
        ("Reject overlap", test_spawn_peg_reject_overlap),
        ("Max pegs", test_spawn_peg_max),
        ("Delete peg", test_delete_peg),
        ("Collision counts", test_collision_counts),
        ("Determinism same seed", test_determinism_same_seed),
        ("Budget limits", test_budget_limits),
        ("SQLite round-trip", test_sqlite_round_trip),
        ("Gravity cycle", test_gravity_cycle),
        ("Reseed", test_reseed),
        ("Headless idempotent", test_headless_idempotent),
        ("Hot peg calc", test_hot_peg),
    ]
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as e:
            print(f"  FAIL  {name}: {e}")
            failures += 1

    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    sys.exit(1 if failures > 0 else 0)
