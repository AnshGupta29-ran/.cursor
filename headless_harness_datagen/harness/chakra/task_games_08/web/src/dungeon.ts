/** Seeded room+corridor vault generator for Deepvault Survey. */

export type Pos = [number, number];

export class Dungeon {
  public map: string[][];
  public width: number;
  public height: number;
  public startPos: Pos = [1, 1];
  public shaftPos: Pos = [1, 1];
  public heartPos: Pos | null = null;
  public currentFloor = 1;
  public visible: Set<string> = new Set();
  public remembered: Set<string> = new Set();
  public items: Map<string, string> = new Map(); // "x,y" -> glyph + o *

  constructor(
    width: number,
    height: number,
    private prng: () => number,
    floor = 1
  ) {
    this.width = width;
    this.height = height;
    this.currentFloor = floor;
    this.map = Array.from({ length: height }, () =>
      Array.from({ length: width }, () => "#")
    );
    this.generate();
  }

  private randInt(lo: number, hi: number): number {
    return lo + Math.floor(this.prng() * (hi - lo + 1));
  }

  private generate() {
    type Room = { x: number; y: number; w: number; h: number; cx: number; cy: number };
    const rooms: Room[] = [];
    const attempts = 30;
    for (let i = 0; i < attempts && rooms.length < 7; i++) {
      const w = this.randInt(4, 8);
      const h = this.randInt(3, 6);
      const x = this.randInt(1, this.width - w - 2);
      const y = this.randInt(1, this.height - h - 2);
      const room = { x, y, w, h, cx: x + Math.floor(w / 2), cy: y + Math.floor(h / 2) };
      const overlaps = rooms.some(
        (r) =>
          !(
            room.x + room.w + 1 < r.x ||
            r.x + r.w + 1 < room.x ||
            room.y + room.h + 1 < r.y ||
            r.y + r.h + 1 < room.y
          )
      );
      if (overlaps) continue;
      for (let yy = y; yy < y + h; yy++) {
        for (let xx = x; xx < x + w; xx++) this.map[yy][xx] = ".";
      }
      if (rooms.length) {
        const prev = rooms[rooms.length - 1];
        this.carveL(prev.cx, prev.cy, room.cx, room.cy);
      }
      rooms.push(room);
    }
    if (!rooms.length) {
      for (let y = 1; y < this.height - 1; y++)
        for (let x = 1; x < this.width - 1; x++) this.map[y][x] = ".";
      this.startPos = [2, 2];
      this.shaftPos = [this.width - 3, this.height - 3];
    } else {
      this.startPos = [rooms[0].cx, rooms[0].cy];
      let far = rooms[0];
      let best = -1;
      for (const r of rooms) {
        const d = Math.abs(r.cx - rooms[0].cx) + Math.abs(r.cy - rooms[0].cy);
        if (d > best) {
          best = d;
          far = r;
        }
      }
      this.shaftPos = [far.cx, far.cy];
    }

    this.map[this.startPos[1]][this.startPos[0]] = ".";
    if (this.currentFloor < 3) {
      this.map[this.shaftPos[1]][this.shaftPos[0]] = ">";
      this.heartPos = null;
    } else {
      this.map[this.shaftPos[1]][this.shaftPos[0]] = "&";
      this.heartPos = [...this.shaftPos] as Pos;
    }

    // place a few items
    const itemGlyphs = ["+", "o", "*"];
    const itemCount = 2 + this.currentFloor;
    for (let i = 0; i < itemCount; i++) {
      const p = this.randomFreePosition();
      const g = itemGlyphs[this.randInt(0, 2)];
      this.items.set(`${p[0]},${p[1]}`, g);
    }
  }

  private carveL(x0: number, y0: number, x1: number, y1: number) {
    let x = x0;
    let y = y0;
    while (x !== x1) {
      this.map[y][x] = ".";
      x += x1 > x ? 1 : -1;
    }
    while (y !== y1) {
      this.map[y][x] = ".";
      y += y1 > y ? 1 : -1;
    }
    this.map[y1][x1] = ".";
  }

  public randomFreePosition(): Pos {
    for (let i = 0; i < 500; i++) {
      const x = this.randInt(1, this.width - 2);
      const y = this.randInt(1, this.height - 2);
      if (this.map[y][x] !== ".") continue;
      if (x === this.startPos[0] && y === this.startPos[1]) continue;
      if (x === this.shaftPos[0] && y === this.shaftPos[1]) continue;
      const key = `${x},${y}`;
      if (this.items.has(key)) continue;
      return [x, y];
    }
    return [this.startPos[0] + 1, this.startPos[1]];
  }

  public walkable(x: number, y: number): boolean {
    if (x < 0 || y < 0 || x >= this.width || y >= this.height) return false;
    return this.map[y][x] !== "#";
  }
}
