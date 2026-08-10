"""Static preview build: autopilot rig under SDL dummy video.

Run:  python -m coretap.preview
Writes preview/site_XX_*.png frames plus preview/index.html contact sheet.
Works with no display (SDL_VIDEODRIVER=dummy is set automatically).
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from .app import project_root  # noqa: E402
from .core.constants import FIXED_DT, HEIGHT, WIDTH  # noqa: E402
from .core.engine import Game  # noqa: E402
from .core.level import load_site  # noqa: E402
from .render import draw as R  # noqa: E402

FRAMES_PER_SITE = 4
TICKS_PER_FRAME = 90


def autopilot(game: Game) -> None:
    """Track the lowest live pulse; launch when attached."""
    live = [p for p in game.pulses]
    if not live:
        return
    if any(p.attached for p in live):
        game.launch()
        return
    target = min(live, key=lambda p: -p.y if p.vy > 0 else 10 ** 9)
    if target.vy > 0:
        err = target.x - game.rig_x
        game.move_rig(max(-1.0, min(1.0, err / 30.0)), FIXED_DT)


def build(out_dir: str | None = None) -> list[str]:
    root = project_root()
    out_dir = out_dir or os.path.join(root, "preview")
    os.makedirs(out_dir, exist_ok=True)
    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT))
    surf = pygame.Surface((WIDTH, HEIGHT))

    levels_dir = os.path.join(root, "levels")
    sites = [load_site(os.path.join(levels_dir, f))
             for f in sorted(os.listdir(levels_dir)) if f.endswith(".json")]
    game = Game(sites, seed=42)
    written: list[str] = []
    for site_i in range(len(sites)):
        while game.site_index < site_i and game.state == "siteclear":
            game.advance_site()
        for frame in range(FRAMES_PER_SITE):
            for _ in range(TICKS_PER_FRAME):
                autopilot(game)
                game.tick(FIXED_DT)
                if game.state != "playing":
                    break
            R.draw_scene(surf, game)
            name = f"site_{site_i+1:02d}_{frame:02d}.png"
            pygame.image.save(surf, os.path.join(out_dir, name))
            written.append(name)
            if game.state == "siteclear":
                game.advance_site()
                break
            if game.state in ("gameover", "win"):
                break
        if game.state in ("gameover", "win"):
            break
    _write_html(out_dir, written)
    pygame.quit()
    return written


def _write_html(out_dir: str, frames: list[str]) -> None:
    imgs = "\n".join(
        f'  <figure><img src="{n}" alt="{n}"><figcaption>{n}</figcaption></figure>'
        for n in frames)
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Core Tap — Abyssal Survey Rig — preview</title>
<style>
 body {{ background:#061220; color:#b2dfd4; font-family:Consolas,monospace;
        margin:2rem; }}
 h1 {{ color:#00e5ff; }}
 figure {{ display:inline-block; margin:8px; }}
 img {{ width:450px; border:1px solid #0d47a1; }}
 figcaption {{ font-size:12px; text-align:center; }}
</style></head><body>
<h1>Core Tap — static preview build</h1>
<p>Autopilot rig, SDL dummy video, fixed seed 42. {len(frames)} frames.</p>
{imgs}
</body></html>"""
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(html)


if __name__ == "__main__":
    names = build()
    print(f"preview: wrote {len(names)} frames + index.html")
