# entity.py
"""Entity definitions for Deepvault Survey roguelike.
Includes Player and three enemy types with specified behaviors.
"""
import random
from typing import Tuple, List

# Helper for Manhattan distance
def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

class Player:
    def __init__(self, start_pos: Tuple[int, int], prng_func):
        self.pos = start_pos
        self.hp = 10
        self.max_hp = 10
        self.attack_damage = 2
        self.prng = prng_func
        # inventory managed separately

    def move(self, dx: int, dy: int, dungeon):
        x, y = self.pos
        nx, ny = x + dx, y + dy
        # bounds check
        if 0 <= nx < dungeon.width and 0 <= ny < dungeon.height:
            if dungeon.map[ny][nx] != "#":
                self.pos = (nx, ny)

class BaseEnemy:
    def __init__(self, glyph: str, hp: int, dmg: int, color: Tuple[int, int, int]):
        self.glyph = glyph
        self.hp = hp
        self.dmg = dmg
        self.color = color
        self.pos: Tuple[int, int] = (0, 0)
        self.state = {}

    def set_position(self, pos: Tuple[int, int]):
        self.pos = pos

    def take_turn(self, player: Player, dungeon, prng_func, entities: List['BaseEnemy']):
        pass

class RustHusk(BaseEnemy):
    """Wanders until player within 5 tiles, then chases via simple BFS step towards player."""
    def __init__(self, pos: Tuple[int, int]):
        super().__init__(glyph='h', hp=4, dmg=1, color=(200, 100, 0))
        self.pos = pos
        self.aware = False

    def take_turn(self, player, dungeon, prng_func, entities):
        if not self.aware:
            if manhattan(self.pos, player.pos) <= 5:
                self.aware = True
        if self.aware:
            # simple greedy step towards player avoiding walls
            px, py = player.pos
            x, y = self.pos
            dx = 1 if px > x else -1 if px < x else 0
            dy = 1 if py > y else -1 if py < y else 0
            # try horizontal move first
            if dx != 0 and dungeon.map[y][x + dx] != '#':
                self.pos = (x + dx, y)
            elif dy != 0 and dungeon.map[y + dy][x] != '#':
                self.pos = (x, y + dy)
        else:
            # wander randomly
            dirs = [(1,0),(-1,0),(0,1),(0,-1)]
            random.shuffle(dirs)
            for dx, dy in dirs:
                nx, ny = self.pos[0] + dx, self.pos[1] + dy
                if 0 <= nx < dungeon.width and 0 <= ny < dungeon.height and dungeon.map[ny][nx] != '#':
                    self.pos = (nx, ny)
                    break
        # attack if adjacent
        if manhattan(self.pos, player.pos) == 1:
            player.hp -= self.dmg

class SentryCoil(BaseEnemy):
    """Immobile; if player shares row/col with clear LOS, telegraphs then zaps next turn."""
    def __init__(self, pos: Tuple[int, int]):
        super().__init__(glyph='s', hp=3, dmg=2, color=(0, 0, 255))
        self.pos = pos
        self.charge = 0  # 0 = idle, 1 = telegraphing

    def line_of_sight(self, player, dungeon):
        px, py = player.pos
        x, y = self.pos
        if x == px:
            step = 1 if py > y else -1
            for ny in range(y + step, py, step):
                if dungeon.map[ny][x] == '#':
                    return False
            return True
        if y == py:
            step = 1 if px > x else -1
            for nx in range(x + step, px, step):
                if dungeon.map[y][nx] == '#':
                    return False
            return True
        return False

    def take_turn(self, player, dungeon, prng_func, entities):
        if self.charge == 1:
            # zap now
            if self.line_of_sight(player, dungeon):
                player.hp -= self.dmg
            self.charge = 0
            return
        if self.line_of_sight(player, dungeon):
            # start telegraph
            self.charge = 1
            # UI can show flashing via state, ignored here

class ScavRat(BaseEnemy):
    """Wanders; consumes items on tile; attacks only when adjacent."""
    def __init__(self, pos: Tuple[int, int]):
        super().__init__(glyph='r', hp=2, dmg=1, color=(150, 75, 0))
        self.pos = pos

    def take_turn(self, player, dungeon, prng_func, entities):
        # wander randomly
        dirs = [(1,0),(-1,0),(0,1),(0,-1)]
        random.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = self.pos[0] + dx, self.pos[1] + dy
            if 0 <= nx < dungeon.width and 0 <= ny < dungeon.height and dungeon.map[ny][nx] != '#':
                self.pos = (nx, ny)
                break
        # attack if adjacent
        if manhattan(self.pos, player.pos) == 1:
            player.hp -= self.dmg
