import type { Game } from "./game";

export class UI {
  private ctx: CanvasRenderingContext2D;
  private tileSize: number;
  private logLines: string[] = [];
  private maxLog = 4;

  constructor(
    _canvas: HTMLCanvasElement,
    ctx: CanvasRenderingContext2D,
    tileSize: number
  ) {
    this.ctx = ctx;
    this.tileSize = tileSize;
  }

  logMessage(msg: string) {
    this.logLines.push(msg);
    if (this.logLines.length > this.maxLog) this.logLines.shift();
  }

  log(msg: string) {
    this.logMessage(msg);
  }

  renderHUD(game: Game) {
    const ctx = this.ctx;
    const yBase = game.mapHeight * this.tileSize + 14;
    ctx.fillStyle = "#9ab";
    ctx.font = "13px monospace";
    if (!game.player) {
      for (let i = 0; i < this.logLines.length; i++) {
        ctx.fillText(this.logLines[this.logLines.length - 1 - i], 8, yBase + 20 + i * 16);
      }
      return;
    }
    ctx.fillStyle = "#cde";
    ctx.fillText(
      `HP ${game.player.hp}/${game.player.maxHp}   D${game.dungeon.currentFloor}/3   Seed ${game.seed}   Turns ${game.turnCount}`,
      8,
      yBase
    );
    if (game.flareTimer > 0) {
      ctx.fillStyle = "#ffcc66";
      ctx.fillText(`Flare ${game.flareTimer}`, 520, yBase);
    }
    for (let i = 0; i < game.inventory.slots.length; i++) {
      const slotX = 8 + i * 70;
      ctx.strokeStyle = "#567";
      ctx.strokeRect(slotX, yBase + 8, 60, 22);
      const item = game.inventory.slots[i];
      ctx.fillStyle = "#ff0";
      ctx.fillText(
        `${i + 1}:${item ? item.glyph + " " + item.name.slice(0, 6) : "-"}`,
        slotX + 4,
        yBase + 24
      );
    }
    ctx.fillStyle = "#8ab";
    for (let i = 0; i < this.logLines.length; i++) {
      const line = this.logLines[this.logLines.length - 1 - i];
      ctx.fillText(line, 230, yBase + 24 + i * 14);
    }
  }
}
