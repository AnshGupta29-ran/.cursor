"""Headless render smoke test: the Pygame front-end draws every screen
without errors using the SDL dummy video driver."""
import os
import sys

import pytest

pygame = pytest.importorskip("pygame")


@pytest.fixture()
def app(monkeypatch, tmp_path):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    from viper_trace import persistence
    monkeypatch.setattr(persistence, "DATA_DIR", tmp_path)
    monkeypatch.setattr(persistence, "SCORES_FILE", tmp_path / "scores.json")
    monkeypatch.setattr(persistence, "SETTINGS_FILE", tmp_path / "settings.json")
    from viper_trace.game import ViperTraceApp
    from viper_trace import game as game_mod
    monkeypatch.setattr(game_mod.persistence, "DATA_DIR", tmp_path)
    monkeypatch.setattr(game_mod.persistence, "SCORES_FILE", tmp_path / "scores.json")
    monkeypatch.setattr(game_mod.persistence, "SETTINGS_FILE", tmp_path / "settings.json")
    application = ViperTraceApp(seed=5)
    yield application
    pygame.quit()


def test_menu_renders(app):
    app._draw_menu()
    pygame.display.flip()


def test_ai_play_and_overlays_render(app):
    from viper_trace.engine import MODE_AI
    app.mode = MODE_AI
    app._start_run()
    for _ in range(30):
        app.engine.tick()
    assert app.engine.hud_status.startswith("TRACE:")
    app._draw_play()
    app.show_explored = True
    app._draw_play()
    app._draw_pause()
    pygame.display.flip()


def test_game_over_screen_renders(app):
    from viper_trace.engine import MODE_MANUAL
    app.mode = MODE_MANUAL
    app._start_run()
    while app.engine.alive:
        app.engine.tick()
    app._draw_game_over()
    pygame.display.flip()
