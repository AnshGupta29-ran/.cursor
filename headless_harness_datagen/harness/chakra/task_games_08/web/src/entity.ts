/** Player + enemies for Deepvault Survey. */

export type Pos = [number, number];

function manhattan(a: Pos, b: Pos): number {
  return Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]);
}

export class Player {
  public pos: Pos;
  public hp = 10;
  public maxHp = 10;
  public attackDamage = 2;
  constructor(startPos: Pos) {
    this.pos = [...startPos] as Pos;
  }
}

export abstract class BaseEnemy {
  public pos: Pos;
  public hp: number;
  public dmg: number;
  public glyph: string;
  public color: string;
  constructor(pos: Pos, glyph: string, hp: number, dmg: number, color: string) {
    this.pos = [...pos] as Pos;
    this.glyph = glyph;
    this.hp = hp;
    this.dmg = dmg;
    this.color = color;
  }
  abstract takeTurn(
    player: Player,
    dungeon: { map: string[][]; width: number; height: number; walkable: (x: number, y: number) => boolean },
    prng: () => number
  ): void;
}

function tryStep(
  pos: Pos,
  dx: number,
  dy: number,
  dungeon: { walkable: (x: number, y: number) => boolean }
): Pos {
  const nx = pos[0] + dx;
  const ny = pos[1] + dy;
  if (dungeon.walkable(nx, ny)) return [nx, ny];
  return pos;
}

export class RustHusk extends BaseEnemy {
  aware = false;
  constructor(pos: Pos, hpScale = 0) {
    super(pos, "h", 4 + hpScale, 1, "#ff8800");
  }
  takeTurn(player, dungeon, prng) {
    if (!this.aware && manhattan(this.pos, player.pos) <= 5) this.aware = true;
    if (this.aware) {
      const dx = Math.sign(player.pos[0] - this.pos[0]);
      const dy = Math.sign(player.pos[1] - this.pos[1]);
      if (dx) this.pos = tryStep(this.pos, dx, 0, dungeon);
      else if (dy) this.pos = tryStep(this.pos, 0, dy, dungeon);
    } else {
      const dirs: Pos[] = [
        [1, 0],
        [-1, 0],
        [0, 1],
        [0, -1],
      ];
      const [dx, dy] = dirs[Math.floor(prng() * 4)];
      this.pos = tryStep(this.pos, dx, dy, dungeon);
    }
    if (manhattan(this.pos, player.pos) === 0 || manhattan(this.pos, player.pos) === 1) {
      // if on same tile after move, step back conceptually — attack adjacent
    }
    if (manhattan(this.pos, player.pos) === 1) player.hp -= this.dmg;
  }
}

export class SentryCoil extends BaseEnemy {
  charge = 0;
  telegraphing = false;
  constructor(pos: Pos, hpScale = 0) {
    super(pos, "s", 3 + hpScale, 2, "#00aaff");
  }
  private hasLOS(player: Player, dungeon: { map: string[][] }): boolean {
    const [px, py] = player.pos;
    const [sx, sy] = this.pos;
    if (px === sx) {
      const step = py > sy ? 1 : -1;
      for (let y = sy + step; y !== py; y += step) if (dungeon.map[y][sx] === "#") return false;
      return true;
    }
    if (py === sy) {
      const step = px > sx ? 1 : -1;
      for (let x = sx + step; x !== px; x += step) if (dungeon.map[sy][x] === "#") return false;
      return true;
    }
    return false;
  }
  takeTurn(player, dungeon, _prng) {
    this.telegraphing = false;
    if (this.charge === 1) {
      if (this.hasLOS(player, dungeon)) player.hp -= this.dmg;
      this.charge = 0;
      return;
    }
    if (this.hasLOS(player, dungeon)) {
      this.charge = 1;
      this.telegraphing = true;
    }
  }
}

export class ScavRat extends BaseEnemy {
  constructor(pos: Pos, hpScale = 0) {
    super(pos, "r", 2 + hpScale, 1, "#aa5500");
  }
  takeTurn(player, dungeon, prng) {
    const dirs: Pos[] = [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
    ];
    const [dx, dy] = dirs[Math.floor(prng() * 4)];
    this.pos = tryStep(this.pos, dx, dy, dungeon);
    if (manhattan(this.pos, player.pos) === 1) player.hp -= this.dmg;
  }
}
