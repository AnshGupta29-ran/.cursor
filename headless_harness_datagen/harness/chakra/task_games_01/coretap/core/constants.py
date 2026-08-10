"""Core Tap — Abyssal Survey Rig. Named constants; no magic numbers elsewhere."""

WIDTH = 900
HEIGHT = 600
FPS = 60
FIXED_DT = 1.0 / FPS

# Rig (paddle)
RIG_WIDTH = 110
RIG_HEIGHT = 16
RIG_Y = HEIGHT - 48
RIG_SPEED = 560.0           # px/s, clamped
WIDE_RIG_FACTOR = 1.6

# Pulse (ball)
PULSE_RADIUS = 7
LAUNCH_SPEED = 360.0        # px/s
SPEEDUP_PER_BRICK = 6.0     # px/s added per fractured brick
SPEED_CAP = 720.0           # hard cap, invariant
MAX_BOUNCE_ANGLE = 65.0     # degrees off vertical at paddle edge

# Modules (power-ups)
MODULE_DROP_RATES = {"ore": 0.35, "other": 0.10}
MODULE_FALL_SPEED = 140.0
MODULE_WIDTH = 34
MODULE_HEIGHT = 18
DRAG_FIELD_SECONDS = 6.0
DRAG_FIELD_FACTOR = 0.55
PIERCE_SECONDS = 5.0
MAX_PULSES = 3
START_HULLS = 3

# Module kinds
M_WIDE = "wide_rig"
M_SPLIT = "split_pulse"
M_DRAG = "drag_field"
M_PIERCE = "pierce_charge"
M_SPARE = "spare_hull"
ALL_MODULES = [M_WIDE, M_SPLIT, M_DRAG, M_PIERCE, M_SPARE]

# Brick classes
BRICK_SPECS = {
    "sediment": {"glyph": "s", "hits": 1, "points": 50, "drop": "other",
                 "color": (96, 125, 139)},
    "ore":      {"glyph": "o", "hits": 1, "points": 150, "drop": "ore",
                 "color": (255, 167, 38)},
    "core":     {"glyph": "c", "hits": 3, "points": 300, "drop": "other",
                 "color": (171, 71, 188)},
    "basalt":   {"glyph": "b", "hits": None, "points": 0, "drop": "other",
                 "color": (38, 50, 56)},
}
GLYPH_TO_CLASS = {v["glyph"]: k for k, v in BRICK_SPECS.items()}

# Palette (abyssal)
COL_BG = (6, 18, 32)
COL_BG2 = (10, 28, 48)
COL_TEXT = (178, 223, 219)
COL_ACCENT = (0, 229, 255)
COL_RIG = (0, 188, 212)
COL_PULSE = (224, 247, 250)
COL_MODULE = (105, 240, 174)
COL_WARN = (255, 82, 82)

# Scoring: depth multiplier per site index (1-based site -> multiplier)
DEPTH_MULTIPLIERS = [1.0, 1.5, 2.0, 2.5, 3.0]

# Files / schema
SCHEMA_VERSION = 1
SNAPSHOT_SLOTS = 3
HIGHSCORE_MAX = 10

SCHEMA_ERROR = "snapshot schema error"
