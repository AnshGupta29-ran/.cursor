# Fathom Fields

Deduction-first harbor sweeping (Minesweeper-grade) — **pygame desktop window**.

## Run

```bash
pip install -r requirements.txt
python main.py          # play
python main.py --smoke  # headless logic checks
```

## Controls

| Input | Action |
|-------|--------|
| Left-click | Sweep (reveal) |
| Right-click | Mark / unmark hazard |
| Shift+Left-click | Chord (open neighbors of a satisfied number) |
| `H` | Hint Buoy — highlights a forced deduction + reason in the log |
| `T` | Cycle theme (Daylight Harbor / Night Watch / Signal Flags) |
| `1` / `2` / `3` | Rowboat / Trawler / Freighter presets |
| `R` | Restart chart |
| `Esc` | Back to menu |

## Presets

- **Rowboat** — 9×9, 10 hazards
- **Trawler** — 16×16, 40 hazards
- **Freighter** — 16×30, 99 hazards

## Hint Buoy

Rule-based only (no guessing):

1. Satisfied number → remaining hidden neighbors are safe water  
2. Remaining count equals hidden neighbors → those cells are certain hazards  
3. Subset rule between overlapping constraints  

If nothing is forced, the log says so honestly.
