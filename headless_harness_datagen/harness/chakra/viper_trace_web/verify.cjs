/* Headless verification of the JS Trace Engine port (run: node verify.cjs).
 * engine.js is a browser classic script; we load it with new Function and
 * return the symbols explicitly. */
"use strict";
const fs = require("fs");
const src = fs.readFileSync(__dirname + "/engine.js", "utf8");
const factory = new Function(src + `
  return { key, manhattan, DIRS, DIR_ORDER, OPPOSITE, makeRng, Grid, aStar,
    simulateMeal, bfsReachable, survivalGate, floodFillArea, fallbackMove,
    AIStatus, traceDecide, nextDirection, borderObstacles, DIFFICULTIES, GameEngine };`);
const {
  key, Grid, aStar, survivalGate, fallbackMove, AIStatus, DIFFICULTIES, GameEngine,
} = factory();

let pass = 0, fail = 0;
function check(name, cond) {
  if (cond) { pass++; console.log("  OK  " + name); }
  else { fail++; console.log("FAIL  " + name); }
}

// A* open-grid shortest
{
  const g = new Grid(10, 10, []);
  const { path } = aStar(g, [0, 0], [5, 3], new Set());
  check("aStar open-grid shortest len 8", path && path.length === 8);
  check("aStar ends at goal", JSON.stringify(path[path.length - 1]) === "[5,3]");
}
// A* around obstacle
{
  const wall = [];
  for (let y = 0; y < 5; y++) if (y !== 4) wall.push([2, y]);
  const g = new Grid(6, 5, wall);
  const { path } = aStar(g, [0, 0], [4, 0], new Set());
  check("aStar routes through gap", path && path.some((c) => c[0] === 2 && c[1] === 4));
}
// A* sealed -> null
{
  const sealed = [[1,1],[3,1],[2,0],[1,2],[3,2],[1,3],[2,3],[3,3]];
  const g = new Grid(5, 5, sealed);
  const { path } = aStar(g, [0, 0], [2, 2], new Set());
  check("aStar sealed returns null", path === null);
}
// survival gate accept/reject
{
  const g = new Grid(10, 10, []);
  const body = [[2,2],[1,2],[0,2]];
  const { path } = aStar(g, [2,2], [8,2], new Set(body.slice(0,-1).map(key)));
  check("gate accepts safe path", survivalGate(g, path, body) === true);
  const g2 = new Grid(3, 3, [[0,0],[2,0]]);
  check("gate rejects trap", survivalGate(g2, [[1,0]], [[1,1],[1,2],[0,2]]) === false);
}
// fallback refuses suicide
{
  const g = new Grid(4, 4, []);
  const cell = fallbackMove(g, [[1,0],[2,0],[3,0],[3,1]]);
  check("fallback picks only safe move", JSON.stringify(cell) === "[1,1]");
}
// fallback null when boxed
{
  const g = new Grid(3, 3, [[1,2]]);
  const cell = fallbackMove(g, [[1,1],[1,0],[0,1],[2,1],[1,2]]);
  check("fallback null when doomed", cell === null);
}
// engine smoke: score > 0 within bounded ticks on all difficulties
{
  for (const k of Object.keys(DIFFICULTIES)) {
    const e = new GameEngine(DIFFICULTIES[k], "ai", 42);
    let t = 0;
    while (t < 3000 && e.score === 0 && e.alive && !e.won) { e.tick(); t++; }
    check(`engine smoke ${DIFFICULTIES[k].name} scores`, e.score > 0);
  }
}
// determinism
{
  const a = new GameEngine(DIFFICULTIES.hatchling, "ai", 7);
  const b = new GameEngine(DIFFICULTIES.hatchling, "ai", 7);
  for (let i = 0; i < 200; i++) { if (a.alive && !a.won) a.tick(); if (b.alive && !b.won) b.tick(); }
  check("deterministic same-seed run", JSON.stringify(a.food) === JSON.stringify(b.food) && a.score === b.score);
}
// fallback fires on a long run
{
  const e = new GameEngine(DIFFICULTIES.viper, "ai", 0);
  let wander = 0;
  for (let i = 0; i < 6000 && e.alive && !e.won; i++) { e.tick(); if (e.aiStatus === AIStatus.SURVIVAL_WANDER) wander++; }
  check("survival wander fires on long run", e.fallbackCount > 0 && wander > 0);
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
