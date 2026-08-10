# game.py
"""Core game loop and orchestration for Deepvault Survey Roguelike.
This module ties together dungeon generation, entity management, FOV, UI,
inventory, and save/restore functionality.
"""

import sys
import pygame
from .dungeon import Dungeon
from .entity import Player, RustHusk, SentryCoil, ScavRat
from .fov import compute_fov
from .inventory import Inventory
from .save import snapshot, restore
from .ui import UI


class Game:
    """Main game class handling initialization, the turn engine, and rendering."""

    TILE_SIZE = 20  # pixels per tile
    MAP_WIDTH = 40
    MAP_HEIGHT = 25
    FPS = 30

    def __init__(self, seed: str | None = None):
        # Initialize pygame and resources
        self.screen = pygame.display.set_mode(
            (self.MAP_WIDTH * self.TILE_SIZE, self.MAP_HEIGHT * self.TILE_SIZE + 80)
        )
        pygame.display.set_caption("Deepvault Survey")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Courier", 16)
        self.small_font = pygame.font.SysFont("Courier", 12)

        # Deterministic PRNG – simple mulberry32 implementation
        self.seed = seed or str(pygame.time.get_ticks())
        self.prng_state = self._seed_to_state(self.seed)
        self.prng = lambda: self._mulberry32()

        # Game state objects
        self.dungeon = Dungeon(self.MAP_WIDTH, self.MAP_HEIGHT, self.prng)
        self.player = Player(self.dungeon.start_pos, self.prng)
        self.entities = []  # enemy list
        self.inventory = Inventory()
        self.ui = UI(self.screen, self.font, self.small_font)
        self.turn_count = 0
        self.flare_timer = 0
        self.stasis_snapshot = None
        self.game_over = False
        self.victory = False

    # ---------------------------------------------------------------------
    # PRNG utilities
    # ---------------------------------------------------------------------
    def _seed_to_state(self, seed: str) -> int:
        # Simple conversion of seed string to 32‑bit integer
        try:
            return int(seed, 36) & 0xffffffff
        except Exception:
            return sum(ord(c) for c in seed) & 0xffffffff

    def _mulberry32(self) -> int:
        # Deterministic 32‑bit PRNG used throughout the game
        self.prng_state = (self.prng_state + 0x6D2B79F5) & 0xffffffff
        t = self.prng_state
        t = (t ^ (t >> 15)) * (t | 1)
        t ^= t + ((t ^ (t >> 7)) * (t | 61))
        return ((t ^ (t >> 14)) & 0xffffffff) / 0xffffffff

    # ---------------------------------------------------------------------
    # Core loop helpers
    # ---------------------------------------------------------------------
    def _spawn_enemies(self):
        """Spawn enemies according to floor depth and deterministic rules.
        For now we add a single RustHusk each 20 turns as a placeholder.
        """
        if self.turn_count % 20 == 0:
            # Place enemy near player but not on player tile
            ex, ey = self.dungeon.random_free_position(self.prng)
            self.entities.append(RustHusk((ex, ey)))

    def _process_player_input(self):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1
        if dx != 0 or dy != 0:
            self.player.move(dx, dy, self.dungeon)
            self._player_attack()
            return True
        return False

    def _player_attack(self):
        # Simple bump‑to‑attack: if an enemy occupies the player's tile, damage it
        px, py = self.player.pos
        for enemy in list(self.entities):
            if enemy.pos == (px, py):
                enemy.hp -= self.player.attack_damage
                if enemy.hp <= 0:
                    self.entities.remove(enemy)
                    self.ui.log_message(f"{enemy.glyph} defeated.")
                else:
                    self.ui.log_message(f"Hit {enemy.glyph}, {enemy.hp} hp left.")
                break

    def _enemies_act(self):
        for enemy in list(self.entities):
            enemy.take_turn(self.player, self.dungeon, self.prng, self.entities)

    def _update_fov(self):
        radius = 12 if self.flare_timer > 0 else 6
        self.visible = compute_fov(self.dungeon.map, self.player.pos, radius)
        if self.flare_timer > 0:
            self.flare_timer -= 1

    def _handle_item_use(self, event_key):
        # 1,2,3 keys use inventory slots
        if event_key in (pygame.K_1, pygame.K_2, pygame.K_3):
            slot = event_key - pygame.K_1
            item = self.inventory.use(slot, self)
            if item:
                self.ui.log_message(f"Used {item.name}.")

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def run(self):
        """Main game loop.
        Handles menu, pause, save/restore, and the turn‑based engine.
        """
        while True:
            self.clock.tick(self.FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._pause_menu()
                    elif event.key == pygame.K_F5:
                        # Stasis Save shortcut
                        self.stasis_snapshot = snapshot(self)
                        self.ui.log_message("Game state saved (stasis).")
                    elif event.key == pygame.K_F9:
                        if self.stasis_snapshot:
                            restore(self, self.stasis_snapshot)
                            self.ui.log_message("Stasis restored.")
                    else:
                        self._handle_item_use(event.key)

            # Player turn – only act when a movement key was pressed
            moved = self._process_player_input()
            if moved:
                self.turn_count += 1
                self._spawn_enemies()
                self._enemies_act()
                self._update_fov()
                self._check_victory_conditions()

            self._render()
            if self.game_over:
                self._end_screen()
                break

    def _pause_menu(self):
        # Simple pause overlay – press any key to resume
        paused = True
        self.ui.draw_overlay("Paused – press any key to resume")
        pygame.display.flip()
        while paused:
            for ev in pygame.event.get():
                if ev.type == pygame.KEYDOWN:
                    paused = False
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            self.clock.tick(10)

    def _check_victory_conditions(self):
        # Victory when player steps on vault heart '&'
        x, y = self.player.pos
        tile = self.dungeon.map[y][x]
        if tile == "&":
            self.victory = True
            self.game_over = True
        if self.player.hp <= 0:
            self.victory = False
            self.game_over = True

    def _render(self):
        self.screen.fill((0, 0, 0))
        # Draw dungeon tiles based on visibility states
        for y in range(self.dungeon.height):
            for x in range(self.dungeon.width):
                glyph = self.dungeon.map[y][x]
                if (x, y) in self.visible:
                    color = (200, 200, 200)
                elif (x, y) in self.dungeon.remembered:
                    color = (80, 80, 80)
                else:
                    continue  # unseen => black
                text = self.font.render(glyph, True, color)
                self.screen.blit(text, (x * self.TILE_SIZE, y * self.TILE_SIZE))
        # Draw player and enemies
        px, py = self.player.pos
        self.screen.blit(self.font.render("@", True, (0, 255, 0)), (px * self.TILE_SIZE, py * self.TILE_SIZE))
        for e in self.entities:
            ex, ey = e.pos
            self.screen.blit(self.font.render(e.glyph, True, e.color), (ex * self.TILE_SIZE, ey * self.TILE_SIZE))
        # HUD
        self.ui.draw_hud(self)
        pygame.display.flip()

    def _end_screen(self):
        # Show victory/defeat screen with score and seed
        self.screen.fill((0, 0, 0))
        msg = "Victory!" if self.victory else "Defeat"
        lines = [msg, f"Score: {self._calculate_score()}", f"Seed: {self.seed}"]
        for i, line in enumerate(lines):
            txt = self.font.render(line, True, (255, 255, 255))
            self.screen.blit(txt, (20, 20 + i * 30))
        pygame.display.flip()
        pygame.time.wait(3000)

    def _calculate_score(self) -> int:
        # Placeholder scoring – can be refined later
        enemies_defeated = sum(1 for e in self.entities if e.hp <= 0)
        items_collected = len(self.inventory.slots)
        depth = self.dungeon.current_floor
        return 25 * enemies_defeated + 15 * items_collected + 100 * depth - self.turn_count
