"""Headless smoke + persistence tests: SDL dummy video, no display needed."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from coretap.core.engine import Game  # noqa: E402
from coretap.core.level import load_site  # noqa: E402
from coretap.core.persistence import (  # noqa: E402
    load_highscores, load_settings, save_highscores, save_settings,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _sites():
    return [load_site(os.path.join(ROOT, "levels", f))
            for f in sorted(os.listdir(os.path.join(ROOT, "levels")))]


def test_smoke_init_and_120_ticks():
    pygame.init()
    pygame.display.set_mode((900, 600))
    from coretap.render import draw as R
    surf = pygame.Surface((900, 600))
    g = Game(_sites(), seed=5)
    g.launch()
    for _ in range(120):
        g.move_rig(0.5, 1 / 60)
        g.tick(1 / 60)
        R.draw_scene(surf, g)
    pygame.quit()


def test_corrupt_highscores_regenerate(tmp_path):
    p = tmp_path / "highscores.json"
    p.write_text("{ not json !!", encoding="utf-8")
    assert load_highscores(str(p)) == []
    save_highscores(str(p), [{"callsign": "RIG", "score": 10, "site": "X"}])
    assert load_highscores(str(p))[0]["score"] == 10


def test_settings_roundtrip(tmp_path):
    p = str(tmp_path / "settings.json")
    assert load_settings(p)["difficulty"] == "standard"
    save_settings(p, {"difficulty": "hard", "mute": True, "game_speed": 1.5})
    s = load_settings(p)
    assert s["difficulty"] == "hard" and s["mute"] and s["game_speed"] == 1.5
