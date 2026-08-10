# inventory.py
"""Inventory system for Deepvault Survey.
Exactly three slots, no stacking. Items have usage effects implemented in this module.
"""
from typing import List, Optional

class Item:
    def __init__(self, name: str, glyph: str):
        self.name = name
        self.glyph = glyph

    def use(self, game):
        """Apply the item's effect on the game instance. Must be overridden."""
        raise NotImplementedError

class PatchKit(Item):
    def __init__(self):
        super().__init__(name="Patch Kit", glyph="+")

    def use(self, game):
        heal = 6
        player = game.player
        player.hp = min(player.max_hp, player.hp + heal)
        game.ui.log_message(f"Patched +{heal} HP.")
        return True

class LumenFlare(Item):
    def __init__(self):
        super().__init__(name="Lumen Flare", glyph="o")
        self.duration = 6

    def use(self, game):
        game.flare_timer = self.duration
        game.ui.log_message("Flare active: vision radius increased.")
        return True

class SparkCharge(Item):
    def __init__(self):
        super().__init__(name="Spark Charge", glyph="*")
        self.damage = 4
        self.radius = 2

    def use(self, game):
        px, py = game.player.pos
        hit = False
        for enemy in list(game.entities):
            ex, ey = enemy.pos
            if abs(ex - px) <= self.radius and abs(ey - py) <= self.radius:
                enemy.hp -= self.damage
                hit = True
                if enemy.hp <= 0:
                    game.entities.remove(enemy)
                    game.ui.log_message(f"{enemy.glyph} destroyed by spark.")
        if not hit:
            game.ui.log_message("Spark fired but hit nothing.")
        return True

class Inventory:
    def __init__(self):
        # slots hold Item or None
        self.slots: List[Optional[Item]] = [None, None, None]

    def add(self, item: Item) -> bool:
        """Add item to first empty slot. Return True if added, False if full."""
        for i in range(3):
            if self.slots[i] is None:
                self.slots[i] = item
                return True
        return False

    def use(self, slot_index: int, game) -> Optional[Item]:
        """Use item at slot_index (0‑based). If used, remove it and return the item.
        Returns None if slot empty.
        """
        if 0 <= slot_index < 3:
            item = self.slots[slot_index]
            if item:
                item.use(game)
                self.slots[slot_index] = None
                return item
        return None
