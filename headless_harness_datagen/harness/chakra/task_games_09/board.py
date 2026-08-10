import random
from typing import List, Tuple, Dict, Set

# Tile representation
TILE_TYPES = {
    'C': ('Crate', '#ff9999'),
    'P': ('Pallet', '#99ff99'),
    'D': ('Drum', '#9999ff'),
    'L': ('Coil', '#ffff99'),
    'S': ('Sack', '#ff99ff'),
}

Tile = str  # one of the keys of TILE_TYPES

class Board:
    def __init__(self, rows: int = 8, cols: int = 8, seed: int = 0):
        self.rows = rows
        self.cols = cols
        self.rng = random.Random(seed)
        self.grid: List[List[Tile]] = [[self._random_tile() for _ in range(cols)] for _ in range(rows)]
        self._remove_initial_matches()
        # guarantee at least one legal move
        if not self.has_legal_move():
            self._shuffle_until_legal()

    def _random_tile(self) -> Tile:
        return self.rng.choice(list(TILE_TYPES.keys()))

    def _remove_initial_matches(self) -> None:
        """Replace tiles that form matches in the initial board.
        Ensures the starting board has no matches.
        """
        while True:
            matches = self.find_matches()
            if not matches:
                break
            for (r, c) in matches:
                self.grid[r][c] = self._random_tile()

    def _shuffle_until_legal(self) -> None:
        # Simple approach: reshuffle whole board until at least one legal move exists
        attempts = 0
        while attempts < 1000:
            flat = [self._random_tile() for _ in range(self.rows * self.cols)]
            self.rng.shuffle(flat)
            self.grid = [flat[i*self.cols:(i+1)*self.cols] for i in range(self.rows)]
            self._remove_initial_matches()
            if self.has_legal_move():
                return
            attempts += 1
        # fallback: leave as is
        return

    def find_matches(self) -> Set[Tuple[int, int]]:
        """Return a set of coordinates (row, col) that are part of a 3+ consecutive line.
        Horizontal and vertical only.
        """
        matches: Set[Tuple[int, int]] = set()
        # Horizontal
        for r in range(self.rows):
            c = 0
            while c < self.cols:
                start = c
                while c + 1 < self.cols and self.grid[r][c] == self.grid[r][c+1]:
                    c += 1
                length = c - start + 1
                if length >= 3:
                    for cc in range(start, c+1):
                        matches.add((r, cc))
                c += 1
        # Vertical
        for c in range(self.cols):
            r = 0
            while r < self.rows:
                start = r
                while r + 1 < self.rows and self.grid[r][c] == self.grid[r+1][c]:
                    r += 1
                length = r - start + 1
                if length >= 3:
                    for rr in range(start, r+1):
                        matches.add((rr, c))
                r += 1
        return matches

    def is_legal_swap(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
        """Check if swapping pos1 and pos2 creates at least one match.
        Positions must be adjacent.
        """
        r1, c1 = pos1
        r2, c2 = pos2
        if abs(r1 - r2) + abs(c1 - c2) != 1:
            return False
        # swap temporarily
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]
        has_match = bool(self.find_matches())
        # swap back
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]
        return has_match

    def swap(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> None:
        r1, c1 = pos1
        r2, c2 = pos2
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]

    def apply_gravity(self) -> int:
        """Make tiles fall down to fill empty spaces.
        Returns number of tiles that fell (used for optional visual effects).
        Empty spaces are represented by None.
        """
        moved = 0
        for c in range(self.cols):
            empty_rows = []
            for r in reversed(range(self.rows)):
                if self.grid[r][c] is None:
                    empty_rows.append(r)
                elif empty_rows:
                    empty_r = empty_rows.pop(0)
                    self.grid[empty_r][c] = self.grid[r][c]
                    self.grid[r][c] = None
                    empty_rows.append(r)
                    moved += 1
            # fill top empty cells with new tiles
            for r in range(len(empty_rows)):
                self.grid[empty_rows[r]][c] = self._random_tile()
                moved += 1
        return moved

    def resolve_cascades(self) -> Tuple[int, int]:
        """Iteratively remove matches, apply gravity, and repeat.
        Returns total_score_gained, total_cascades (multiplier count).
        Scoring: each tile cleared gives 10 points * current multiplier.
        Multiplier starts at 1 and increments each cascade step.
        """
        total_score = 0
        cascade_step = 0
        while True:
            matches = self.find_matches()
            if not matches:
                break
            cascade_step += 1
            points = len(matches) * 10 * cascade_step
            total_score += points
            # remove matched tiles (set to None)
            for (r, c) in matches:
                self.grid[r][c] = None
            self.apply_gravity()
        return total_score, cascade_step

    def has_legal_move(self) -> bool:
        """Check if any adjacent swap would create a match."""
        for r in range(self.rows):
            for c in range(self.cols):
                if c + 1 < self.cols and self.is_legal_swap((r, c), (r, c+1)):
                    return True
                if r + 1 < self.rows and self.is_legal_swap((r, c), (r+1, c)):
                    return True
        return False

    def copy(self) -> 'Board':
        """Return a deep copy of the board (used for testing)."""
        new_board = Board(self.rows, self.cols, seed=0)
        new_board.grid = [row[:] for row in self.grid]
        new_board.rng = self.rng
        return new_board

# Simple level data structure
class Level:
    def __init__(self, level_id: int, seed: int, quota: int, moves: int, rows: int = 8, cols: int = 8):
        self.id = level_id
        self.seed = seed
        self.quota = quota
        self.moves = moves
        self.rows = rows
        self.cols = cols
        self.board = Board(rows, cols, seed)
