/**
 * Deepvault Survey — playable browser core.
 */
import { Dungeon } from "./dungeon";
import {
  Player,
  RustHusk,
  SentryCoil,
  ScavRat,
  BaseEnemy,
  type Pos,
} from "./entity";
import { computeFOV } from "./fov";
import { Inventory, PatchKit, LumenFlare, SparkCharge, Item } from "./inventory";
import { UI } from "./ui";
import { snapshot, restore } from "./save";

type Mode = "menu" | "play" | "pause" | "end";

export class Game {
  canvas: HTMLCanvasElement;
  ctx: CanvasRenderingContext2D;
  tileSize = 16;
  mapWidth = 48;
  mapHeight = 28;
  seed = "";
  prngState = 0;
  prng: () => number = () => 0;

  dungeon!: Dungeon;
  player!: Player;
  entities: BaseEnemy[] = [];
  inventory = new Inventory();
  ui: UI;

  turnCount = 0;
  flareTimer = 0;
  gameOver = false;
  victory = false;
  enemiesDefeated = 0;
  itemsCollected = 0;
  stasisSnapshot: any = null;
  mode: Mode = "menu";
  seedInput = "";
  menuIndex = 0;

  constructor(canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D) {
    this.canvas = canvas;
    this.ctx = ctx;
    this.ui = new UI(canvas, ctx, this.tileSize);
    this.canvas.width = this.mapWidth * this.tileSize;
    this.canvas.height = this.mapHeight * this.tileSize + 96;
    window.addEventListener("keydown", (e) => this.handleKey(e));
    this.render();
  }

  private seedToState(seed: string): number {
    let h = 2166136261;
    for (let i = 0; i < seed.length; i++) {
      h ^= seed.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  private mulberry32(): number {
    this.prngState = (this.prngState + 0x6d2b79f5) >>> 0;
    let t = this.prngState;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }

  start() {
    const loop = () => {
      this.render();
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  private newRun(seed?: string) {
    this.seed = (seed && seed.trim()) || Math.random().toString(36).slice(2, 8).toUpperCase();
    this.prngState = this.seedToState(this.seed);
    this.prng = () => this.mulberry32();
    this.turnCount = 0;
    this.flareTimer = 0;
    this.gameOver = false;
    this.victory = false;
    this.enemiesDefeated = 0;
    this.itemsCollected = 0;
    this.inventory = new Inventory();
    this.loadFloor(1);
    this.mode = "play";
    this.ui.log(`Expedition seed ${this.seed}. Recover the Vault Heart.`);
  }

  private loadFloor(floor: number) {
    this.dungeon = new Dungeon(this.mapWidth, this.mapHeight, this.prng, floor);
    this.player = new Player(this.dungeon.startPos);
    this.entities = [];
    const scale = floor - 1;
    const counts = [
      { n: 2 + floor, make: (p: Pos) => new RustHusk(p, scale) },
      { n: 1 + Math.floor(floor / 2), make: (p: Pos) => new SentryCoil(p, scale) },
      { n: 2 + floor, make: (p: Pos) => new ScavRat(p, scale) },
    ];
    for (const c of counts) {
      for (let i = 0; i < c.n; i++) {
        const pos = this.dungeon.randomFreePosition();
        this.entities.push(c.make(pos));
      }
    }
    this.updateFOV();
  }

  handleKey(e: KeyboardEvent) {
    if (this.mode === "menu") {
      if (e.key === "ArrowUp" || e.key === "w") this.menuIndex = (this.menuIndex + 2) % 3;
      if (e.key === "ArrowDown" || e.key === "s") this.menuIndex = (this.menuIndex + 1) % 3;
      if (/^[a-zA-Z0-9]$/.test(e.key) && this.menuIndex === 0) {
        if (this.seedInput.length < 12) this.seedInput += e.key.toUpperCase();
      }
      if (e.key === "Backspace" && this.menuIndex === 0) this.seedInput = this.seedInput.slice(0, -1);
      if (e.key === "Enter") {
        if (this.menuIndex === 0) this.newRun(this.seedInput || undefined);
        else if (this.menuIndex === 1) {
          if (this.stasisSnapshot) {
            restore(this, this.stasisSnapshot);
            this.mode = "play";
            this.ui.log("Stasis restored.");
          } else this.ui.log("No stasis snapshot in this tab.");
        } else {
          this.ui.log("WASD/Arrows move · bump attack · 1-3 items · F5 stasis · F9 resume · Esc pause");
        }
      }
      return;
    }

    if (this.mode === "end") {
      if (e.key === "Enter" || e.key === " ") {
        this.mode = "menu";
        this.seedInput = "";
      }
      return;
    }

    if (this.mode === "pause") {
      if (e.key === "Escape" || e.key === "p" || e.key === "P") this.mode = "play";
      if (e.key === "F5") {
        this.stasisSnapshot = snapshot(this);
        this.ui.log("Stasis save captured (memory only — lost on refresh).");
      }
      if (e.key === "F9" && this.stasisSnapshot) {
        restore(this, this.stasisSnapshot);
        this.mode = "play";
        this.ui.log("Stasis restored.");
      }
      return;
    }

    if (this.mode !== "play" || this.gameOver) return;

    if (e.key === "Escape" || e.key === "p" || e.key === "P") {
      this.mode = "pause";
      return;
    }
    if (e.key === "F5") {
      e.preventDefault();
      this.stasisSnapshot = snapshot(this);
      this.ui.log("Stasis save captured (tab memory only).");
      return;
    }
    if (e.key === "F9") {
      e.preventDefault();
      if (this.stasisSnapshot) {
        restore(this, this.stasisSnapshot);
        this.ui.log("Stasis restored.");
      } else this.ui.log("No stasis yet.");
      return;
    }
    if (e.key === "1") {
      this.inventory.use(0, this);
      return;
    }
    if (e.key === "2") {
      this.inventory.use(1, this);
      return;
    }
    if (e.key === "3") {
      this.inventory.use(2, this);
      return;
    }

    let dx = 0;
    let dy = 0;
    const k = e.key.toLowerCase();
    if (k === "arrowup" || k === "w" || k === "k") dy = -1;
    else if (k === "arrowdown" || k === "s" || k === "j") dy = 1;
    else if (k === "arrowleft" || k === "a" || k === "h") dx = -1;
    else if (k === "arrowright" || k === "d" || k === "l") dx = 1;
    else if (k === "y") {
      dx = -1;
      dy = -1;
    } else if (k === "u") {
      dx = 1;
      dy = -1;
    } else if (k === "b") {
      dx = -1;
      dy = 1;
    } else if (k === "n") {
      dx = 1;
      dy = 1;
    } else return;

    e.preventDefault();
    this.playerAct(dx, dy);
  }

  private playerAct(dx: number, dy: number) {
    const nx = this.player.pos[0] + dx;
    const ny = this.player.pos[1] + dy;
    if (!this.dungeon.walkable(nx, ny)) return;

    const enemy = this.entities.find((en) => en.pos[0] === nx && en.pos[1] === ny);
    if (enemy) {
      enemy.hp -= this.player.attackDamage;
      this.ui.log(`You strike ${enemy.glyph} (${enemy.hp} hp).`);
      if (enemy.hp <= 0) {
        this.entities = this.entities.filter((e) => e !== enemy);
        this.enemiesDefeated++;
        this.ui.log(`${enemy.glyph} falls apart.`);
      }
    } else {
      this.player.pos = [nx, ny];
      this.pickup();
      const tile = this.dungeon.map[ny][nx];
      if (tile === ">" && this.dungeon.currentFloor < 3) {
        this.ui.log(`Descending to vault depth ${this.dungeon.currentFloor + 1}...`);
        this.loadFloor(this.dungeon.currentFloor + 1);
        this.turnCount++;
        this.enemiesAct();
        this.tickStatus();
        this.updateFOV();
        this.checkEnd();
        return;
      }
      if (tile === "&") {
        this.victory = true;
        this.gameOver = true;
        this.mode = "end";
        this.ui.log("Vault Heart recovered!");
        return;
      }
    }

    this.turnCount++;
    this.enemiesAct();
    this.tickStatus();
    this.updateFOV();
    this.checkEnd();
  }

  private pickup() {
    const key = `${this.player.pos[0]},${this.player.pos[1]}`;
    const g = this.dungeon.items.get(key);
    if (!g) return;
    let item: Item | null = null;
    if (g === "+") item = new PatchKit();
    else if (g === "o") item = new LumenFlare();
    else if (g === "*") item = new SparkCharge();
    if (!item) return;
    if (this.inventory.add(item)) {
      this.dungeon.items.delete(key);
      this.itemsCollected++;
      this.ui.log(`Salvaged ${item.name}.`);
    } else {
      this.ui.log("Inventory full — leave the salvage.");
    }
  }

  private enemiesAct() {
    for (const e of [...this.entities]) {
      if (e.hp <= 0) continue;
      // don't walk onto other enemies / player tile for movement simplicity
      const before = [...e.pos] as Pos;
      e.takeTurn(this.player, this.dungeon, this.prng);
      // prevent stacking on player by attack-only if moved onto player
      if (e.pos[0] === this.player.pos[0] && e.pos[1] === this.player.pos[1]) {
        e.pos = before;
        this.player.hp -= e.dmg;
        this.ui.log(`${e.glyph} hits you!`);
      }
      // scav rats eat items
      if (e instanceof ScavRat) {
        const k = `${e.pos[0]},${e.pos[1]}`;
        if (this.dungeon.items.has(k)) {
          this.dungeon.items.delete(k);
          this.ui.log("Scav Rat consumes a salvage!");
        }
      }
    }
  }

  private tickStatus() {
    if (this.flareTimer > 0) this.flareTimer--;
  }

  private updateFOV() {
    const radius = this.flareTimer > 0 ? 12 : 6;
    const vis = computeFOV(this.dungeon.map, this.player.pos, radius);
    this.dungeon.visible = vis;
    for (const k of vis) this.dungeon.remembered.add(k);
  }

  private checkEnd() {
    if (this.player.hp <= 0) {
      this.player.hp = 0;
      this.victory = false;
      this.gameOver = true;
      this.mode = "end";
      this.ui.log("Signal Lost.");
    }
  }

  calculateScore(): number {
    return Math.max(
      0,
      25 * this.enemiesDefeated +
        15 * this.itemsCollected +
        100 * this.dungeon.currentFloor -
        this.turnCount
    );
  }

  private render() {
    const ctx = this.ctx;
    ctx.fillStyle = "#05080c";
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    if (this.mode === "menu") {
      ctx.fillStyle = "#7dffb3";
      ctx.font = "22px monospace";
      ctx.fillText("DEEPVAULT SURVEY", 40, 60);
      ctx.fillStyle = "#9ab";
      ctx.font = "14px monospace";
      ctx.fillText("Recover the Vault Heart across 3 flooded data floors.", 40, 90);
      const opts = [
        `New Expedition  seed:[${this.seedInput || "auto"}]`,
        `Resume Stasis${this.stasisSnapshot ? "" : " (empty)"}`,
        "How to Play",
      ];
      opts.forEach((o, i) => {
        ctx.fillStyle = i === this.menuIndex ? "#fff" : "#678";
        ctx.fillText(`${i === this.menuIndex ? ">" : " "} ${o}`, 40, 140 + i * 28);
      });
      ctx.fillStyle = "#567";
      ctx.fillText("Up/Down select · type seed · Enter confirm", 40, 260);
      this.ui.renderHUD(this);
      return;
    }

    if (this.mode === "end") {
      ctx.fillStyle = this.victory ? "#7dffb3" : "#f66";
      ctx.font = "24px monospace";
      ctx.fillText(this.victory ? "VAULT HEART SECURED" : "SIGNAL LOST", 40, 80);
      ctx.fillStyle = "#ccc";
      ctx.font = "16px monospace";
      ctx.fillText(`Salvage score: ${this.calculateScore()}`, 40, 120);
      ctx.fillText(`Seed: ${this.seed}`, 40, 150);
      ctx.fillText(`Turns: ${this.turnCount}  Depth: ${this.dungeon.currentFloor}/3`, 40, 180);
      ctx.fillText("Enter — return to menu", 40, 230);
      return;
    }

    // play / pause map
    for (let y = 0; y < this.dungeon.height; y++) {
      for (let x = 0; x < this.dungeon.width; x++) {
        const key = `${x},${y}`;
        const visible = this.dungeon.visible.has(key);
        const remembered = this.dungeon.remembered.has(key);
        if (!visible && !remembered) continue;
        let glyph = this.dungeon.map[y][x];
        const item = this.dungeon.items.get(key);
        if (item && (visible || remembered)) glyph = item;
        ctx.fillStyle = visible ? "#cde" : "#445";
        if (glyph === "#") ctx.fillStyle = visible ? "#6a8" : "#234";
        if (glyph === ">") ctx.fillStyle = visible ? "#ffcc66" : "#664";
        if (glyph === "&") ctx.fillStyle = visible ? "#ff66cc" : "#623";
        if (item) ctx.fillStyle = visible ? "#ff0" : "#660";
        ctx.font = `${this.tileSize}px monospace`;
        ctx.fillText(glyph, x * this.tileSize, (y + 1) * this.tileSize);
      }
    }

    for (const e of this.entities) {
      const key = `${e.pos[0]},${e.pos[1]}`;
      if (!this.dungeon.visible.has(key)) continue;
      ctx.fillStyle =
        e instanceof SentryCoil && (e as SentryCoil).telegraphing ? "#fff" : e.color;
      ctx.fillText(e.glyph, e.pos[0] * this.tileSize, (e.pos[1] + 1) * this.tileSize);
    }

    ctx.fillStyle = "#7dffb3";
    ctx.fillText("@", this.player.pos[0] * this.tileSize, (this.player.pos[1] + 1) * this.tileSize);

    this.ui.renderHUD(this);

    if (this.mode === "pause") {
      ctx.fillStyle = "rgba(0,0,0,0.65)";
      ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      ctx.fillStyle = "#fff";
      ctx.font = "20px monospace";
      ctx.fillText("PAUSED — Esc continue · F5 Stasis · F9 Resume", 40, 80);
    }
  }
}


