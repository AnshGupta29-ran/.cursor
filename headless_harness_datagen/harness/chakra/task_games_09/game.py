# UI imports are done lazily in run_gui to avoid side‑effects during headless execution
import json
import os
from typing import Tuple, List
from board import Board, Level, TILE_TYPES

# Constants for UI layout
CELL_SIZE = 60
PANEL_WIDTH = 200
WINDOW_WIDTH = CELL_SIZE * 8 + PANEL_WIDTH
WINDOW_HEIGHT = CELL_SIZE * 8

# Path to persistence files
SAVE_PATH = os.path.join(os.path.dirname(__file__), "save.json")
LEVELS_PATH = os.path.join(os.path.dirname(__file__), "levels.json")

class SaveData:
    def __init__(self):
        self.settings = {}
        self.best_scores = {}
        self.last_run = {}
        self._load()

    def _load(self):
        if os.path.exists(SAVE_PATH):
            try:
                with open(SAVE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.settings = data.get("settings", {})
                    self.best_scores = data.get("best_scores", {})
                    self.last_run = data.get("last_run", {})
            except Exception:
                # corrupt file – reset
                self.settings = {}
                self.best_scores = {}
                self.last_run = {}
        else:
            self._write()

    def _write(self):
        tmp_path = SAVE_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump({
                "settings": self.settings,
                "best_scores": self.best_scores,
                "last_run": self.last_run,
            }, f, indent=2)
        os.replace(tmp_path, SAVE_PATH)

    def update_score(self, level_id: int, score: int):
        best = self.best_scores.get(str(level_id), 0)
        if score > best:
            self.best_scores[str(level_id)] = score
            self._write()

    def record_last(self, level_id: int, result: str, score: int):
        self.last_run = {
            "level_id": level_id,
            "result": result,
            "score": score,
        }
        self._write()

class Game:
    def __init__(self, root: tk.Tk, level_data: dict):
        self.root = root
        self.level = Level(**level_data)
        self.board = self.level.board
        self.score = 0
        self.moves_left = self.level.moves
        self.quota = self.level.quota
        self.cursor: Tuple[int, int] = (0, 0)  # row, col
        self.selected: Tuple[int, int] | None = None
        self.log: List[str] = []
        self.save = SaveData()
        self._setup_ui()
        self._update_ui()
        self.root.bind("<Key>", self._on_key)

    def _setup_ui(self):
        self.root.title("DockSort: Shift Quota")
        self.canvas = tk.Canvas(self.root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        self.canvas.pack()
        # Create a text widget for log on the right side
        self.log_widget = tk.Text(self.root, width=30, height=20, state="disabled", wrap="word")
        self.log_widget.place(x=CELL_SIZE * 8 + 10, y=10)
        # Score / moves labels
        self.score_label = ttk.Label(self.root, text="Score: 0")
        self.score_label.place(x=CELL_SIZE * 8 + 10, y=300)
        self.moves_label = ttk.Label(self.root, text=f"Moves: {self.moves_left}")
        self.moves_label.place(x=CELL_SIZE * 8 + 10, y=330)
        self.quota_label = ttk.Label(self.root, text=f"Quota: {self.quota}")
        self.quota_label.place(x=CELL_SIZE * 8 + 10, y=360)

    def _draw_board(self):
        self.canvas.delete("all")
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                x1 = c * CELL_SIZE
                y1 = r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                tile = self.board.grid[r][c]
                name, color = TILE_TYPES[tile]
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")
                self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=tile, font=("Helvetica", 20, "bold"))
        # highlight cursor
        cr, cc = self.cursor
        self.canvas.create_rectangle(cc * CELL_SIZE, cr * CELL_SIZE, (cc + 1) * CELL_SIZE, (cr + 1) * CELL_SIZE, outline="red", width=3)
        # highlight selected tile if any
        if self.selected:
            sr, sc = self.selected
            self.canvas.create_rectangle(sc * CELL_SIZE, sr * CELL_SIZE, (sc + 1) * CELL_SIZE, (sr + 1) * CELL_SIZE, outline="blue", width=3)

    def _log(self, message: str):
        self.log.append(message)
        self.log_widget.configure(state="normal")
        self.log_widget.insert(tk.END, message + "\n")
        self.log_widget.configure(state="disabled")
        self.log_widget.see(tk.END)

    def _on_key(self, event):
        key = event.keysym
        if key in ("Up", "Down", "Left", "Right"):
            self._move_cursor(key)
        elif key == "space":
            self._select_or_swap()
        elif key == "h" or key == "H":
            self._hint()
        elif key == "p" or key == "P":
            self._pause()
        elif key == "r" or key == "R":
            self._restart()
        elif key == "m" or key == "M":
            # mute is no-op for now
            pass
        elif key == "F1":
            self._toggle_contrast()
        # ignore other keys
        self._update_ui()

    def _move_cursor(self, direction: str):
        r, c = self.cursor
        if direction == "Up" and r > 0:
            r -= 1
        elif direction == "Down" and r < self.board.rows - 1:
            r += 1
        elif direction == "Left" and c > 0:
            c -= 1
        elif direction == "Right" and c < self.board.cols - 1:
            c += 1
        self.cursor = (r, c)

    def _select_or_swap(self):
        if self.selected is None:
            # select current cursor
            self.selected = self.cursor
            self._log(f"Selected {self._tile_name(self.selected)} at {self._pos_str(self.selected)}")
        else:
            # attempt swap with previously selected if adjacent
            if self._are_adjacent(self.selected, self.cursor):
                self._attempt_swap(self.selected, self.cursor)
            else:
                self._log("Tiles not adjacent; selection cleared.")
            self.selected = None

    def _are_adjacent(self, a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

    def _attempt_swap(self, pos1: Tuple[int, int], pos2: Tuple[int, int]):
        if not self.board.is_legal_swap(pos1, pos2):
            self._log(f"Illegal swap between {self._pos_str(pos1)} and {self._pos_str(pos2)}; move refunded.")
            # illegal swaps still consume a move? spec says refund move, so we don't decrement.
            return
        # legal swap
        self.board.swap(pos1, pos2)
        self.moves_left -= 1
        self._log(f"Swapped {self._pos_str(pos1)} with {self._pos_str(pos2)}")
        # resolve cascades and update score
        added_score, cascades = self.board.resolve_cascades()
        self.score += added_score
        self._log(f"Match! +{added_score} pts, cascade ×{cascades}")
        self._check_end_conditions()

    def _check_end_conditions(self):
        if self.score >= self.quota:
            self._log("Quota reached! You win!")
            self.save.update_score(self.level.id, self.score)
            self.save.record_last(self.level.id, "win", self.score)
            self._show_end_screen(True)
        elif self.moves_left <= 0:
            self._log("Out of moves. You lose.")
            self.save.record_last(self.level.id, "lose", self.score)
            self._show_end_screen(False)
        else:
            # continue
            pass

    def _show_end_screen(self, won: bool):
        msg = "Victory!" if won else "Defeat"
        self._log(msg)
        # Disable further input
        self.root.unbind("<Key>")
        # Simple popup
        popup = tk.Toplevel(self.root)
        popup.title(msg)
        ttk.Label(popup, text=msg, font=("Helvetica", 16)).pack(padx=20, pady=10)
        ttk.Button(popup, text="Restart", command=lambda: [popup.destroy(), self._restart()]).pack(pady=5)
        ttk.Button(popup, text="Quit", command=self.root.destroy).pack(pady=5)

    def _hint(self):
        # Find first legal move and highlight it
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                if c + 1 < self.board.cols and self.board.is_legal_swap((r, c), (r, c + 1)):
                    self._log(f"Hint: swap {self._pos_str((r, c))} right.")
                    return
                if r + 1 < self.board.rows and self.board.is_legal_swap((r, c), (r + 1, c)):
                    self._log(f"Hint: swap {self._pos_str((r, c))} down.")
                    return
        self._log("No legal moves found; reshuffling.")
        self.board._shuffle_until_legal()

    def _pause(self):
        # Simple pause toggle using a modal dialog
        paused = tk.Toplevel(self.root)
        paused.title("Paused")
        ttk.Label(paused, text="Game paused. Press any key to continue.").pack(padx=20, pady=20)
        paused.bind("<Key>", lambda e: paused.destroy())
        paused.focus_set()
        paused.grab_set()
        self.root.wait_window(paused)

    def _restart(self):
        # Recreate board with same level parameters
        self.board = Board(self.level.rows, self.level.cols, self.level.seed)
        self.score = 0
        self.moves_left = self.level.moves
        self.cursor = (0, 0)
        self.selected = None
        self.log.clear()
        self.log_widget.configure(state="normal")
        self.log_widget.delete("1.0", tk.END)
        self.log_widget.configure(state="disabled")
        self._log("Game restarted.")
        self._update_ui()

    def _toggle_contrast(self):
        # Simple high-contrast toggle by inverting colors
        # Not fully implemented; placeholder log
        self._log("High-contrast mode toggled (placeholder).")

    def _tile_name(self, pos: Tuple[int, int]) -> str:
        r, c = pos
        tile = self.board.grid[r][c]
        return TILE_TYPES[tile][0]

    def _pos_str(self, pos: Tuple[int, int]) -> str:
        r, c = pos
        return f"({r},{c})"

    def _update_ui(self):
        self._draw_board()
        self.score_label.config(text=f"Score: {self.score}")
        self.moves_label.config(text=f"Moves: {self.moves_left}")
        self.quota_label.config(text=f"Quota: {self.quota}")

def load_levels() -> List[dict]:
    if not os.path.exists(LEVELS_PATH):
        # create default levels if missing
        default = [
            {"level_id": 1, "seed": 42, "quota": 500, "moves": 30},
            {"level_id": 2, "seed": 123, "quota": 800, "moves": 25},
            {"level_id": 3, "seed": 999, "quota": 1200, "moves": 20},
        ]
        with open(LEVELS_PATH, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default
    with open(LEVELS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    root = tk.Tk()
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    levels = load_levels()
    # Simple menu: choose first level for now
    game = Game(root, levels[0])
    root.mainloop()

if __name__ == "__main__":
    main()
