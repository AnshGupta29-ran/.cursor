/* Viper Trace — Trace Engine (pure logic, no rendering).
 * Ported from viper_trace/ai/trace_engine.py + engine.py.
 * A* (4-neighborhood, Manhattan) -> survival gate -> flood-fill fallback. */
"use strict";

// ---------------------------------------------------------------- utilities
const key = (c) => c[0] + "," + c[1];
const manhattan = (a, b) => Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]);

const DIRS = { UP: [0, -1], RIGHT: [1, 0], DOWN: [0, 1], LEFT: [-1, 0] };
const DIR_ORDER = ["UP", "RIGHT", "DOWN", "LEFT"]; // fixed N,E,S,W
const OPPOSITE = { UP: "DOWN", DOWN: "UP", LEFT: "RIGHT", RIGHT: "LEFT" };

// Seeded RNG (mulberry32) so --seed-equivalent runs are reproducible.
function makeRng(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// --------------------------------------------------------------------- grid
class Grid {
  constructor(width, height, obstacles) {
    this.width = width;
    this.height = height;
    this.obstacles = new Set((obstacles || []).map(key));
  }
  inBounds(c) { return c[0] >= 0 && c[0] < this.width && c[1] >= 0 && c[1] < this.height; }
  isBlocked(c) { return !this.inBounds(c) || this.obstacles.has(key(c)); }
  neighbors(c) {
    const out = [];
    for (const d of DIR_ORDER) {
      const n = [c[0] + DIRS[d][0], c[1] + DIRS[d][1]];
      if (this.inBounds(n)) out.push(n);
    }
    return out;
  }
}

// ----------------------------------------------------------------- A* search
function aStar(grid, start, goal, extraBlocked) {
  const blocked = (c) => grid.isBlocked(c) || extraBlocked.has(key(c));
  if (blocked(goal)) return { path: null, closed: new Set() };

  // binary heap of [f, counter, cell]
  const heap = [];
  const push = (item) => {
    heap.push(item);
    let i = heap.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (heap[p][0] < heap[i][0] || (heap[p][0] === heap[i][0] && heap[p][1] <= heap[i][1])) break;
      [heap[p], heap[i]] = [heap[i], heap[p]]; i = p;
    }
  };
  const pop = () => {
    const top = heap[0], last = heap.pop();
    if (heap.length) {
      heap[0] = last;
      let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = l + 1;
        let s = i;
        if (l < heap.length && (heap[l][0] < heap[s][0] || (heap[l][0] === heap[s][0] && heap[l][1] < heap[s][1]))) s = l;
        if (r < heap.length && (heap[r][0] < heap[s][0] || (heap[r][0] === heap[s][0] && heap[r][1] < heap[s][1]))) s = r;
        if (s === i) break;
        [heap[s], heap[i]] = [heap[i], heap[s]]; i = s;
      }
    }
    return top;
  };

  const gScore = new Map([[key(start), 0]]);
  const cameFrom = new Map();
  const closed = new Set();
  let counter = 0;
  push([manhattan(start, goal), counter++, start]);

  while (heap.length) {
    const [, , current] = pop();
    const ck = key(current);
    if (ck === key(goal)) {
      const path = [current];
      let cur = current;
      while (cameFrom.has(key(cur))) { cur = cameFrom.get(key(cur)); path.push(cur); }
      path.reverse();
      return { path: path.slice(1), closed };
    }
    if (closed.has(ck)) continue;
    closed.add(ck);
    for (const d of DIR_ORDER) {
      const n = [current[0] + DIRS[d][0], current[1] + DIRS[d][1]];
      const nk = key(n);
      if (!grid.inBounds(n) || blocked(n) || closed.has(nk)) continue;
      const tentative = gScore.get(ck) + 1;
      if (tentative < (gScore.has(nk) ? gScore.get(nk) : Infinity)) {
        gScore.set(nk, tentative);
        cameFrom.set(nk, current);
        push([tentative + manhattan(n, goal), counter++, n]);
      }
    }
  }
  return { path: null, closed };
}

// ------------------------------------------------------------ survival logic
function simulateMeal(body, path) {
  const b = body.slice();
  for (let i = 0; i < path.length; i++) {
    b.unshift(path[i]);
    if (i < path.length - 1) b.pop();
  }
  return b;
}

function bfsReachable(grid, start, goal, blockedSet) {
  if (key(start) === key(goal)) return true;
  const visited = new Set([key(start)]);
  const q = [start];
  while (q.length) {
    const cur = q.shift();
    for (const n of grid.neighbors(cur)) {
      if (key(n) === key(goal)) return true;
      const nk = key(n);
      if (visited.has(nk) || blockedSet.has(nk) || grid.isBlocked(n)) continue;
      visited.add(nk);
      q.push(n);
    }
  }
  return false;
}

function survivalGate(grid, path, body) {
  if (!path || !path.length) return false;
  const post = simulateMeal(body, path);
  const blocked = new Set(post.slice(1).map(key));
  const freeCells = grid.width * grid.height - grid.obstacles.size;
  if (post.length >= freeCells) return true; // board full: win
  return bfsReachable(grid, post[0], post[post.length - 1], blocked);
}

function floodFillArea(grid, start, blockedSet) {
  if (grid.isBlocked(start) || blockedSet.has(key(start))) return 0;
  const visited = new Set([key(start)]);
  const q = [start];
  let count = 0;
  while (q.length) {
    const cur = q.shift();
    count++;
    for (const n of grid.neighbors(cur)) {
      const nk = key(n);
      if (visited.has(nk) || blockedSet.has(nk) || grid.isBlocked(n)) continue;
      visited.add(nk);
      q.push(n);
    }
  }
  return count;
}

function fallbackMove(grid, body) {
  const head = body[0], tail = body[body.length - 1];
  const bodySet = new Set(body.map(key));
  const candidates = [];
  for (let order = 0; order < DIR_ORDER.length; order++) {
    const d = DIR_ORDER[order];
    const n = [head[0] + DIRS[d][0], head[1] + DIRS[d][1]];
    if (grid.isBlocked(n) || (bodySet.has(key(n)) && key(n) !== key(tail))) continue;
    const newBody = [n].concat(body.slice(0, -1));
    const newBlocked = new Set(newBody.slice(1).map(key));
    const safe = (key(newBody[0]) === key(newBody[newBody.length - 1])) ||
      bfsReachable(grid, newBody[0], newBody[newBody.length - 1], newBlocked) ? 1 : 0;
    const area = floodFillArea(grid, n, newBlocked);
    candidates.push({ safe, area, order, cell: n });
  }
  if (!candidates.length) return null;
  candidates.sort((a, b) => b.safe - a.safe || b.area - a.area || a.order - b.order);
  return candidates[0].cell;
}

const AIStatus = { SAFE_ROUTE: "SAFE ROUTE", SURVIVAL_WANDER: "SURVIVAL WANDER", NO_PATH: "NO PATH" };

function traceDecide(grid, body, food) {
  const head = body[0], tail = body[body.length - 1];
  const bodySet = new Set(body.map(key));
  bodySet.delete(key(tail));
  const { path, closed } = aStar(grid, head, food, bodySet);
  if (path && survivalGate(grid, path, body)) return { status: AIStatus.SAFE_ROUTE, path, closed };
  const fb = fallbackMove(grid, body);
  if (fb) return { status: AIStatus.SURVIVAL_WANDER, path: [fb], closed };
  return { status: AIStatus.NO_PATH, path: [], closed };
}

function nextDirection(head, next) {
  const dx = next[0] - head[0], dy = next[1] - head[1];
  for (const d of DIR_ORDER) if (DIRS[d][0] === dx && DIRS[d][1] === dy) return d;
  return null;
}

// ------------------------------------------------------------ difficulties
function borderObstacles(w, h) {
  const obs = [];
  for (let x = 0; x < w; x++) { obs.push([x, 0], [x, h - 1]); }
  for (let y = 1; y < h - 1; y++) { obs.push([0, y], [w - 1, y]); }
  return obs;
}
const DIFFICULTIES = {
  hatchling: { name: "Hatchling", width: 20, height: 20, startSpeed: 8, minSpeed: 4, maxSpeed: 12,
    obstacles: borderObstacles(20, 20), scoreMultiplier: 1 },
  viper: { name: "Viper", width: 30, height: 25, startSpeed: 10, minSpeed: 6, maxSpeed: 14,
    obstacles: borderObstacles(30, 25).concat(Array.from({length: 15}, (_, i) => [10, i + 5])), scoreMultiplier: 2 },
  apex: { name: "Apex", width: 40, height: 30, startSpeed: 12, minSpeed: 8, maxSpeed: 16,
    obstacles: borderObstacles(40, 30)
      .concat(Array.from({length: 15}, (_, i) => [15, i + 10]))
      .concat(Array.from({length: 15}, (_, i) => [25, i + 5])), scoreMultiplier: 3 },
};

// ---------------------------------------------------------------- engine
class GameEngine {
  constructor(difficulty, mode, seed) {
    this.difficulty = difficulty;
    this.mode = mode; // "manual" | "ai"
    this.grid = new Grid(difficulty.width, difficulty.height, difficulty.obstacles);
    this.rng = makeRng(seed === undefined ? (Math.random() * 2 ** 31) | 0 : seed);
    let cx = difficulty.width >> 1, cy = difficulty.height >> 1;
    while (this.grid.isBlocked([cx, cy])) cx++;
    this.snake = [[cx, cy], [cx - 1, cy], [cx - 2, cy]];
    this.direction = "RIGHT";
    this.appliedDir = "RIGHT";
    this.queue = [];
    this.growPending = 0;
    this.speed = difficulty.startSpeed;
    this.score = 0; this.ticks = 0; this.pellets = 0; this.fallbackCount = 0;
    this.alive = true; this.won = false;
    this.aiStatus = null; this.aiPath = []; this.aiClosed = new Set();
    this.food = null;
    this._placeFood();
  }
  _placeFood() {
    const free = [];
    const bodySet = new Set(this.snake.map(key));
    for (let x = 0; x < this.grid.width; x++)
      for (let y = 0; y < this.grid.height; y++) {
        const c = [x, y];
        if (!this.grid.isBlocked(c) && !bodySet.has(key(c))) free.push(c);
      }
    if (!free.length) { this.food = null; this.won = true; return; }
    this.food = free[(this.rng() * free.length) | 0];
  }
  queueDirection(dir) {
    if (!this.alive) return;
    const base = this.queue.length ? this.queue[this.queue.length - 1] : this.appliedDir;
    if (OPPOSITE[dir] === base) return;
    if (this.queue.length < 3) this.queue.push(dir);
  }
  adjustSpeed(delta) {
    this.speed = Math.max(this.difficulty.minSpeed, Math.min(this.speed + delta, this.difficulty.maxSpeed));
  }
  _move() {
    const d = DIRS[this.direction];
    const head = [this.snake[0][0] + d[0], this.snake[0][1] + d[1]];
    if (this.grid.isBlocked(head)) return false;
    const bodyNoTail = this.snake.slice(0, -1);
    if (bodyNoTail.some((c) => key(c) === key(head))) return false;
    this.snake.unshift(head);
    if (this.growPending > 0) this.growPending--;
    else this.snake.pop();
    return true;
  }
  tick() {
    if (!this.alive || this.won) return;
    this.ticks++;
    if (this.mode === "ai" && this.food) {
      const result = traceDecide(this.grid, this.snake, this.food);
      this.aiStatus = result.status; this.aiPath = result.path; this.aiClosed = result.closed;
      let dir = null;
      if (result.status === AIStatus.SAFE_ROUTE) dir = nextDirection(this.snake[0], result.path[0]);
      else if (result.status === AIStatus.SURVIVAL_WANDER) { this.fallbackCount++; dir = nextDirection(this.snake[0], result.path[0]); }
      if (dir && OPPOSITE[dir] !== this.direction) { this.direction = dir; this.appliedDir = dir; }
    } else if (this.queue.length) {
      const dir = this.queue.shift();
      if (OPPOSITE[dir] !== this.direction) { this.direction = dir; this.appliedDir = dir; }
    }
    if (!this._move()) { this.alive = false; return; }
    if (this.food && key(this.snake[0]) === key(this.food)) {
      this.growPending++;
      this.pellets++;
      this.score += this.difficulty.scoreMultiplier;
      this._placeFood();
      if (this.mode === "ai" && this.food) {
        const r = traceDecide(this.grid, this.snake, this.food);
        this.aiStatus = r.status; this.aiPath = r.path; this.aiClosed = r.closed;
      }
    }
  }
  get length() { return this.snake.length; }
  get hudStatus() {
    if (this.mode !== "ai") return "TRACE: MANUAL";
    return this.aiStatus ? "TRACE: " + this.aiStatus : "TRACE: --";
  }
}

