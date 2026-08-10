"""Application controller: screens, input, audio, persistence glue."""
from __future__ import annotations

import os
import time

import pygame

from .core.constants import (
    COL_ACCENT, COL_TEXT, COL_WARN, FIXED_DT, FPS, HEIGHT, HIGHSCORE_MAX,
    SNAPSHOT_SLOTS, WIDTH,
)
from .core.engine import Game
from .core.level import LevelError, load_site
from .core.persistence import (
    atomic_write_json, load_highscores, load_settings, save_highscores,
    save_settings,
)
from .core.snapshot import SnapshotError, load_snapshot_file, save_snapshot
from .render import draw as R


def project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _p(*parts: str) -> str:
    return os.path.join(project_root(), *parts)


class Beeper:
    """Generated beeps; silent if the mixer is unavailable."""

    def __init__(self, muted: bool = False):
        self.ok = False
        self.muted = muted
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            pygame.mixer.init(44100, -16, 1, 256)
            import array
            for name, freq in (("brick", 660), ("module", 880),
                               ("lost", 180), ("clear", 990)):
                n = 4410
                samples = array.array("h", (
                    int(12000 * (1.0 if (i * freq // 100) % 2 else -1.0)
                        * (1 - i / n))
                    for i in range(n)))
                self.sounds[name] = pygame.mixer.Sound(buffer=samples.tobytes())
            self.ok = True
        except pygame.error:
            self.ok = False

    def play(self, name: str) -> None:
        if self.ok and not self.muted and name in self.sounds:
            self.sounds[name].play()


class App:
    def __init__(self, headless: bool = False):
        pygame.init()
        flags = 0
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        pygame.display.set_caption("Core Tap — Abyssal Survey Rig")
        self.clock = pygame.time.Clock()
        self.settings = load_settings(_p("saves", "settings.json"))
        self.beeper = Beeper(self.settings["mute"])
        self.scores = load_highscores(_p("saves", "highscores.json"))
        self.sites = self._load_sites()
        self.mode = "menu"          # menu | playing | paused | clear | over | enter
        self.game: Game | None = None
        self.notice = ""
        self.notice_until = 0.0
        self.callsign = ""
        self.headless = headless
        self.running = True

    def _load_sites(self):
        sites = []
        levels_dir = _p("levels")
        for name in sorted(os.listdir(levels_dir)):
            if name.endswith(".json"):
                try:
                    sites.append(load_site(os.path.join(levels_dir, name)))
                except LevelError as exc:
                    self._say(str(exc))
        return sites

    def _say(self, msg: str, secs: float = 3.0) -> None:
        self.notice = msg
        self.notice_until = time.time() + secs

    def new_run(self) -> None:
        if not self.sites:
            self._say("no valid sites loaded; check levels/", 5)
            return
        seed = int(time.time() * 1000) % (2 ** 31)
        self.game = Game(self.sites, seed=seed)
        self.mode = "playing"
        self.beeper.play("clear")

    # ----- snapshots -----------------------------------------------------------
    def export(self, slot: int = 1) -> None:
        if not self.game:
            return
        path = _p("saves", f"snapshot_{slot}.json")
        save_snapshot(path, self.game.export_snapshot())
        self._say(f"survey snapshot exported -> saves/snapshot_{slot}.json")

    def import_(self, slot: int = 1) -> None:
        path = _p("saves", f"snapshot_{slot}.json")
        try:
            snap = load_snapshot_file(path)
            self.game = Game.import_snapshot(self.sites, snap)
            self.mode = "paused"
            self._say("survey snapshot restored")
        except (SnapshotError, IndexError) as exc:
            self._say(f"snapshot rejected: {exc}", 5)

    # ----- main loop -----------------------------------------------------------
    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._events()
            if self.mode == "playing" and self.game:
                self._input(dt)
                self._step()
            self._draw()
        self.shutdown()

    def _step(self) -> None:
        speed = self.settings["game_speed"]
        events = self.game.tick(FIXED_DT * speed)
        for ev in events:
            if ev.kind == "brick":
                self.beeper.play("brick")
            elif ev.kind == "module":
                self.beeper.play("module")
            elif ev.kind == "lost":
                self.beeper.play("lost")
            elif ev.kind in ("clear", "win"):
                self.beeper.play("clear")
        if self.game.state == "siteclear":
            self.mode = "clear"
        elif self.game.state == "gameover":
            self._finish_run()
        elif self.game.state == "win":
            self._finish_run()

    def _finish_run(self) -> None:
        self.mode = "enter"
        self.callsign = ""

    def _commit_score(self) -> None:
        tag = (self.callsign or "RIG")[:3].upper()
        self.scores.append({"callsign": tag, "score": self.game.score,
                            "site": self.game.site.name})
        self.scores = sorted(self.scores, key=lambda e: -e["score"])[:HIGHSCORE_MAX]
        save_highscores(_p("saves", "highscores.json"), self.scores)
        self.mode = "over"

    def _input(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        d = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            d -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            d += 1
        self.game.move_rig(d, dt * self.settings["game_speed"])

    def _events(self) -> None:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
                continue
            if ev.type != pygame.KEYDOWN:
                continue
            k = ev.key
            if self.mode == "menu":
                if k in (pygame.K_RETURN, pygame.K_SPACE):
                    self.new_run()
                elif k == pygame.K_ESCAPE:
                    self.running = False
            elif self.mode == "playing":
                if k == pygame.K_SPACE and self.game:
                    self.game.launch()
                elif k in (pygame.K_p, pygame.K_ESCAPE):
                    self.mode = "paused"
                elif k == pygame.K_F5:
                    self.export(1)
                elif k == pygame.K_F9:
                    self.import_(1)
            elif self.mode == "paused":
                if k in (pygame.K_p, pygame.K_ESCAPE):
                    self.mode = "playing"
                elif k == pygame.K_F5:
                    self.export(1)
                elif k == pygame.K_F9:
                    self.import_(1)
                elif k == pygame.K_m:
                    self.mode = "menu"
            elif self.mode == "clear":
                if k in (pygame.K_RETURN, pygame.K_SPACE):
                    self.game.advance_site()
                    self.mode = "playing"
            elif self.mode == "enter":
                if k == pygame.K_RETURN:
                    self._commit_score()
                elif k == pygame.K_BACKSPACE:
                    self.callsign = self.callsign[:-1]
                elif k == pygame.K_ESCAPE:
                    self._commit_score()
                elif len(self.callsign) < 3 and ev.unicode.isalnum():
                    self.callsign += ev.unicode.upper()
            elif self.mode == "over":
                if k == pygame.K_r:
                    self.new_run()
                elif k == pygame.K_ESCAPE:
                    self.mode = "menu"

    # ----- drawing -------------------------------------------------------------
    def _draw(self) -> None:
        if self.mode == "menu":
            self.screen.fill((6, 18, 32))
            R.overlay(self.screen, [
                ("Pilot the survey rig. Fracture strata. Extract ore.", 20,
                 COL_TEXT),
                ("", 10, COL_TEXT),
                ("LEFT/RIGHT or A/D — move rig", 18, COL_TEXT),
                ("SPACE — launch pulse / start run", 18, COL_TEXT),
                ("P or ESC — pause survey", 18, COL_TEXT),
                ("F5 export snapshot    F9 import snapshot", 18, COL_ACCENT),
                ("", 10, COL_TEXT),
                ("PRESS ENTER TO DIVE", 24, COL_ACCENT),
            ], "CORE TAP")
            self._draw_scores(430)
        else:
            R.draw_scene(self.screen, self.game)
            if self.mode == "paused":
                R.overlay(self.screen, [
                    ("Survey suspended — physics and module timers frozen.",
                     18, COL_TEXT),
                    ("LEFT/RIGHT or A/D — move rig    SPACE — launch pulse",
                     18, COL_TEXT),
                    ("P/ESC resume    F5 export    F9 import    M menu",
                     18, COL_ACCENT),
                ], "PAUSED")
            elif self.mode == "clear":
                R.overlay(self.screen, [
                    (f"Site {self.game.site.name} fully fractured.", 20,
                     COL_TEXT),
                    (f"Ore tally: {self.game.score}", 20, COL_ACCENT),
                    ("ENTER — descend to next site", 20, COL_TEXT),
                ], "SITE CLEAR")
            elif self.mode == "enter":
                outcome = ("SURVEY COMPLETE" if self.game.state == "win"
                           else "RIG LOST")
                R.overlay(self.screen, [
                    (f"Final ore tally: {self.game.score}", 22, COL_TEXT),
                    (f"Callsign: {self.callsign}_", 26, COL_ACCENT),
                    ("3 chars, ENTER to log    ESC to skip", 16, COL_TEXT),
                ], outcome)
            elif self.mode == "over":
                R.overlay(self.screen, [
                    (f"Ore tally logged: {self.game.score}", 22, COL_TEXT),
                    ("R — re-dive    ESC — surface (menu)", 18, COL_ACCENT),
                ], "RUN LOGGED")
                self._draw_scores(300)
        if time.time() < self.notice_until and self.notice:
            R.text(self.screen, self.notice, 15, COL_WARN, WIDTH // 2,
                   HEIGHT - 20, True)
        pygame.display.flip()

    def _draw_scores(self, y0: int) -> None:
        R.text(self.screen, "— TOP SURVEYORS —", 16, COL_ACCENT, WIDTH // 2,
               y0, True)
        for i, e in enumerate(self.scores[:10]):
            R.text(self.screen,
                   f"{i+1:2d}. {e['callsign']:<3} {e['score']:07d}  {e['site']}",
                   15, COL_TEXT, WIDTH // 2, y0 + 24 + i * 18, True)

    def shutdown(self) -> None:
        # flush on any exit path, incl. window close mid-run
        save_settings(_p("saves", "settings.json"), self.settings)
        save_highscores(_p("saves", "highscores.json"), self.scores)
        pygame.quit()


def main() -> None:
    App().run()
