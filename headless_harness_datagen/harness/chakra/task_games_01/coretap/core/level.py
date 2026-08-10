"""Level (drill site) loading and validation. Glyph grids: s/o/c/b/."""
from __future__ import annotations

import json
from dataclasses import dataclass

from .constants import GLYPH_TO_CLASS, WIDTH


class LevelError(Exception):
    """Raised on malformed level JSON; message names file and field."""


@dataclass
class Site:
    name: str
    depth_m: int
    grid: list[list[str]]          # brick-class names or "" for empty
    speed_ramp: float              # multiplier applied to launch speed
    path: str = ""

    @property
    def destructible_count(self) -> int:
        return sum(1 for row in self.grid for c in row if c and c != "basalt")


def _err(path: str, field: str, msg: str) -> LevelError:
    return LevelError(f"level '{path}': field '{field}': {msg}")


def load_site(path: str) -> Site:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise LevelError(f"level '{path}': unreadable JSON: {exc}") from exc
    return parse_site(data, path)


def parse_site(data: dict, path: str = "<memory>") -> Site:
    if not isinstance(data, dict):
        raise _err(path, "<root>", "expected object")
    name = data.get("name")
    if not isinstance(name, str) or not name:
        raise _err(path, "name", "must be non-empty string")
    depth = data.get("depth_m")
    if not isinstance(depth, int) or depth < 0:
        raise _err(path, "depth_m", "must be non-negative int")
    rows = data.get("grid")
    if not isinstance(rows, list) or not rows or not all(isinstance(r, str) for r in rows):
        raise _err(path, "grid", "must be non-empty list of strings")
    width = len(rows[0])
    if width == 0:
        raise _err(path, "grid", "rows must be non-empty")
    grid: list[list[str]] = []
    for i, row in enumerate(rows):
        if len(row) != width:
            raise _err(path, "grid", f"row {i} length {len(row)} != {width}")
        parsed = []
        for ch in row:
            if ch == ".":
                parsed.append("")
            elif ch in GLYPH_TO_CLASS:
                parsed.append(GLYPH_TO_CLASS[ch])
            else:
                raise _err(path, "grid", f"unknown glyph {ch!r} in row {i}")
        grid.append(parsed)
    ramp = data.get("speed_ramp", 1.0)
    if not isinstance(ramp, (int, float)) or not (0.5 <= ramp <= 3.0):
        raise _err(path, "speed_ramp", "must be number in [0.5, 3.0]")
    drops = data.get("drop_table", {})
    if not isinstance(drops, dict):
        raise _err(path, "drop_table", "must be object")
    return Site(name=name, depth_m=depth, grid=grid, speed_ramp=float(ramp), path=path)


def brick_geometry(site: Site, top: int = 90, side: int = 40, gap: int = 6):
    """Yield (col, row, x, y, w, h) layout for a site grid."""
    cols = len(site.grid[0])
    bw = (WIDTH - 2 * side - (cols - 1) * gap) / cols
    bh = 22.0
    for r, row in enumerate(site.grid):
        for c, cls in enumerate(row):
            if cls:
                x = side + c * (bw + gap)
                y = top + r * (bh + gap)
                yield c, r, x, y, bw, bh
