import type { Game } from "./game";
import { RustHusk, SentryCoil, ScavRat } from "./entity";
import { PatchKit, LumenFlare, SparkCharge } from "./inventory";

export function snapshot(game: Game): any {
  return JSON.parse(
    JSON.stringify({
      seed: game.seed,
      prngState: game.prngState,
      turnCount: game.turnCount,
      flareTimer: game.flareTimer,
      enemiesDefeated: game.enemiesDefeated,
      itemsCollected: game.itemsCollected,
      player: {
        pos: [...game.player.pos],
        hp: game.player.hp,
        maxHp: game.player.maxHp,
        attackDamage: game.player.attackDamage,
      },
      dungeon: {
        map: game.dungeon.map.map((row) => [...row]),
        width: game.dungeon.width,
        height: game.dungeon.height,
        startPos: [...game.dungeon.startPos],
        shaftPos: [...game.dungeon.shaftPos],
        currentFloor: game.dungeon.currentFloor,
        visible: Array.from(game.dungeon.visible),
        remembered: Array.from(game.dungeon.remembered),
        items: Array.from(game.dungeon.items.entries()),
      },
      entities: game.entities.map((e) => ({
        glyph: e.glyph,
        hp: e.hp,
        dmg: e.dmg,
        pos: [...e.pos],
        type: e.constructor.name,
        telegraphing: (e as any).telegraphing || false,
        charge: (e as any).charge || 0,
        aware: (e as any).aware || false,
      })),
      inventory: {
        slots: game.inventory.slots.map((it) => (it ? { type: it.constructor.name } : null)),
      },
      gameOver: game.gameOver,
      victory: game.victory,
    })
  );
}

export function restore(game: Game, state: any) {
  game.seed = state.seed;
  game.prngState = state.prngState;
  game.prng = () => {
    game.prngState = (game.prngState + 0x6d2b79f5) >>> 0;
    let t = game.prngState;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  game.turnCount = state.turnCount;
  game.flareTimer = state.flareTimer;
  game.enemiesDefeated = state.enemiesDefeated || 0;
  game.itemsCollected = state.itemsCollected || 0;
  game.player.pos = [...state.player.pos];
  game.player.hp = state.player.hp;
  game.player.maxHp = state.player.maxHp;
  game.player.attackDamage = state.player.attackDamage;
  game.dungeon.map = state.dungeon.map.map((row: string[]) => [...row]);
  game.dungeon.width = state.dungeon.width;
  game.dungeon.height = state.dungeon.height;
  game.dungeon.startPos = [...state.dungeon.startPos];
  game.dungeon.shaftPos = [...state.dungeon.shaftPos];
  game.dungeon.currentFloor = state.dungeon.currentFloor;
  game.dungeon.visible = new Set(state.dungeon.visible);
  game.dungeon.remembered = new Set(state.dungeon.remembered);
  game.dungeon.items = new Map(state.dungeon.items || []);
  const typeMap: Record<string, any> = { RustHusk, SentryCoil, ScavRat };
  game.entities = state.entities.map((e: any) => {
    const ctor = typeMap[e.type] || RustHusk;
    const inst = new ctor(e.pos);
    inst.hp = e.hp;
    inst.dmg = e.dmg;
    if ("aware" in inst) (inst as any).aware = e.aware;
    if ("charge" in inst) (inst as any).charge = e.charge;
    if ("telegraphing" in inst) (inst as any).telegraphing = e.telegraphing;
    return inst;
  });
  const itemMap: Record<string, any> = { PatchKit, LumenFlare, SparkCharge };
  game.inventory.slots = state.inventory.slots.map((s: any) =>
    s ? new itemMap[s.type]() : null
  );
  game.gameOver = state.gameOver;
  game.victory = state.victory;
  game.mode = "play";
}
