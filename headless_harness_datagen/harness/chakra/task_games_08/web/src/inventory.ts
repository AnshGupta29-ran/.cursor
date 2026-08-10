import type { Game } from "./game";

export abstract class Item {
  abstract name: string;
  abstract glyph: string;
  abstract use(game: Game): void;
}

export class PatchKit extends Item {
  name = "Patch Kit";
  glyph = "+";
  use(game: Game) {
    const heal = 6;
    game.player.hp = Math.min(game.player.maxHp, game.player.hp + heal);
    game.ui.log(`Patched +${heal} HP.`);
  }
}

export class LumenFlare extends Item {
  name = "Lumen Flare";
  glyph = "o";
  use(game: Game) {
    game.flareTimer = 6;
    game.ui.log("Lumen flare — vision expanded.");
  }
}

export class SparkCharge extends Item {
  name = "Spark Charge";
  glyph = "*";
  use(game: Game) {
    const [px, py] = game.player.pos;
    let hit = false;
    for (let i = game.entities.length - 1; i >= 0; i--) {
      const e = game.entities[i];
      if (Math.abs(e.pos[0] - px) <= 2 && Math.abs(e.pos[1] - py) <= 2) {
        e.hp -= 4;
        hit = true;
        if (e.hp <= 0) {
          game.entities.splice(i, 1);
          game.enemiesDefeated++;
          game.ui.log(`${e.glyph} destroyed by spark.`);
        }
      }
    }
    if (!hit) game.ui.log("Spark wasted — no husks in range.");
  }
}

export class Inventory {
  slots: (Item | null)[] = [null, null, null];
  add(item: Item): boolean {
    for (let i = 0; i < this.slots.length; i++) {
      if (!this.slots[i]) {
        this.slots[i] = item;
        return true;
      }
    }
    return false;
  }
  use(slotIdx: number, game: Game): void {
    const item = this.slots[slotIdx];
    if (!item) {
      game.ui.log("Empty slot.");
      return;
    }
    item.use(game);
    this.slots[slotIdx] = null;
  }
}
