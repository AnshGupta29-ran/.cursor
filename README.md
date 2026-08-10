# Minesweeper Console Game

A pure‑Python, console‑based implementation of Minesweeper with:

- **Difficulty presets** – Beginner (8×8, 10 mines), Intermediate (16×16, 40 mines), Expert (30×16, 99 mines).
- **First‑click safety** – the first revealed cell is never a mine, and its neighbours are also safe.
- **Deterministic hint system** – up to 5 hints per game. The engine analyses the board and highlights a safe cell that can be proven safe using simple logical deduction (if a numbered cell already has the required mines flagged, the remaining hidden neighbours are safe).
- **High‑score tracking** – best time per difficulty is saved between sessions.
- **Settings persistence** – hint mode can be toggled and the last difficulty is remembered.

## Controls (console)
```
reveal r c   – uncover cell at row r, column c
flag   r c   – toggle flag on cell
hint          – request a hint (if enabled and hints remain)
quit          – abort the current game
```
Rows and columns are **0‑based**.

## Running the game
```bash
python main.py
```
The script will present a small text menu:
1. Play Game
2. View High Scores
3. Settings (toggle hint mode)
4. Quit

## Files
- `main.py` – full source code.
- `minesweeper_settings.json` – generated automatically; stores settings and high scores.
- `README.md` – this document.

## License
Public domain / MIT – feel free to modify and extend.
