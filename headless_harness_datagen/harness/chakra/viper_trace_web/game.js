/* Viper Trace — Canvas front-end: menus, HUD, overlays. */
"use strict";

const CELL = 24, HUD_H = 64, HELP_H = 28;
const C = {
  bg: "#0d1117", panel: "#161b22", grid: "#1e242d", wall: "#586375",
  head: "#3fe078", body: "#239655", food: "#ffab2e", accent: "#ffab2e",
  path: "#ffd25a", explored: "rgba(60,90,130,0.28)", text: "#dce4ee",
  dim: "#8c98a8", danger: "#f05454",
};

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const urlSeed = new URLSearchParams(location.search).get("seed");
const app = {
  state: "menu", // menu | playing | paused | game_over
  mode: "manual",
  diffKeys: Object.keys(DIFFICULTIES),
  diffIndex: 0,
  menuIndex: 0,
  engine: null,
  showExplored: true,
  newBest: false,
  seed: urlSeed === null ? undefined : parseInt(urlSeed, 10),
  lastTick: 0,
};
app.difficulty = DIFFICULTIES[app.diffKeys[app.diffIndex]];

// persistence (localStorage)
const store = {
  best: (d, m) => parseInt(localStorage.getItem(`vt_best_${d}_${m}`) || "0", 10),
  saveBest(d, m, s) {
    if (s > store.best(d, m)) { localStorage.setItem(`vt_best_${d}_${m}`, s); return true; }
    return false;
  },
  load() {
    try { return JSON.parse(localStorage.getItem("vt_settings") || "{}"); } catch { return {}; }
  },
  save(s) { localStorage.setItem("vt_settings", JSON.stringify(s)); },
};
const saved = store.load();
if (saved.difficulty && DIFFICULTIES[saved.difficulty]) {
  app.diffIndex = app.diffKeys.indexOf(saved.difficulty);
  app.difficulty = DIFFICULTIES[app.diffIndex];
}
if (typeof saved.showExplored === "boolean") app.showExplored = saved.showExplored;

function persistSettings() {
  store.save({ difficulty: app.diffKeys[app.diffIndex], showExplored: app.showExplored,
    speed: { ...(saved.speed || {}), [app.difficulty.name]: app.engine ? app.engine.speed : app.difficulty.startSpeed } });
}

function resize() {
  canvas.width = app.difficulty.width * CELL;
  canvas.height = app.difficulty.height * CELL + HUD_H + HELP_H;
}
resize();

function startRun() {
  app.engine = new GameEngine(app.difficulty, app.mode, app.seed);
  const sp = (saved.speed || {})[app.difficulty.name];
  if (sp) app.engine.speed = Math.max(app.difficulty.minSpeed, Math.min(sp, app.difficulty.maxSpeed));
  app.newBest = false;
  app.state = "playing";
  app.lastTick = performance.now();
  resize();
}

// ---------------------------------------------------------------- drawing
function text(s, x, y, size, color, align = "left") {
  ctx.fillStyle = color;
  ctx.font = `${size}px 'Courier New', monospace`;
  ctx.textAlign = align;
  ctx.textBaseline = "top";
  ctx.fillText(s, x, y);
}
function cellRect(c) { return [c[0] * CELL, HUD_H + c[1] * CELL, CELL, CELL]; }

function drawMenu() {
  ctx.fillStyle = C.bg; ctx.fillRect(0, 0, canvas.width, canvas.height);
  const w = canvas.width;
  text("VIPER TRACE", w / 2, 50, 48, C.head, "center");
  text("A* Snake Observatory", w / 2, 105, 18, C.dim, "center");
  const opts = ["Manual Mode", "AI Mode (Trace Engine)", "Quit"];
  opts.forEach((o, i) => {
    const sel = i === app.menuIndex;
    text((sel ? "> " : "  ") + o, w / 2 - 140, 170 + i * 34, 20, sel ? C.accent : C.text);
  });
  const d = app.difficulty;
  text(`Difficulty: < ${d.name} >  (${d.width}x${d.height}, ${d.obstacles.length} walls, x${d.scoreMultiplier})`,
    w / 2, 300, 18, C.accent, "center");
  text(`Best — manual: ${store.best(d.name, "manual")}   ai: ${store.best(d.name, "ai")}`,
    w / 2, 334, 14, C.dim, "center");
  text("Up/Down select · Left/Right difficulty · Enter start", w / 2, 390, 13, C.dim, "center");
}

function drawPlay() {
  const e = app.engine, d = app.difficulty;
  ctx.fillStyle = C.bg; ctx.fillRect(0, 0, canvas.width, canvas.height);
  // grid
  ctx.strokeStyle = C.grid; ctx.lineWidth = 1;
  for (let x = 0; x <= d.width; x++) { ctx.beginPath(); ctx.moveTo(x * CELL, HUD_H); ctx.lineTo(x * CELL, HUD_H + d.height * CELL); ctx.stroke(); }
  for (let y = 0; y <= d.height; y++) { ctx.beginPath(); ctx.moveTo(0, HUD_H + y * CELL); ctx.lineTo(d.width * CELL, HUD_H + y * CELL); ctx.stroke(); }
  // obstacles
  ctx.fillStyle = C.wall;
  for (const o of d.obstacles) { const [x, y, w, h] = cellRect(o); ctx.fillRect(x, y, w, h); }
  // explored tint
  if (e.mode === "ai" && app.showExplored) {
    ctx.fillStyle = C.explored;
    for (const k of e.aiClosed) { const [cx, cy] = k.split(",").map(Number); ctx.fillRect(cx * CELL, HUD_H + cy * CELL, CELL, CELL); }
  }
  // path
  if (e.mode === "ai" && e.aiPath.length) {
    const col = e.aiStatus === AIStatus.SAFE_ROUTE ? C.path : C.danger;
    ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 3;
    ctx.beginPath();
    const pts = [e.snake[0]].concat(e.aiPath);
    pts.forEach((c, i) => { const px = c[0] * CELL + CELL / 2, py = HUD_H + c[1] * CELL + CELL / 2; i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); });
    ctx.stroke();
    for (let i = 1; i < pts.length; i++) { ctx.beginPath(); ctx.arc(pts[i][0] * CELL + CELL / 2, HUD_H + pts[i][1] * CELL + CELL / 2, 3, 0, 7); ctx.fill(); }
  }
  // food
  if (e.food) { ctx.fillStyle = C.food; ctx.beginPath(); ctx.arc(e.food[0] * CELL + CELL / 2, HUD_H + e.food[1] * CELL + CELL / 2, CELL / 3, 0, 7); ctx.fill(); }
  // snake
  e.snake.forEach((c, i) => {
    ctx.fillStyle = i === 0 ? C.head : C.body;
    ctx.fillRect(c[0] * CELL + 1, HUD_H + c[1] * CELL + 1, CELL - 2, CELL - 2);
  });
  // HUD
  ctx.fillStyle = C.panel; ctx.fillRect(0, 0, canvas.width, HUD_H);
  text(`Score ${e.score}`, 10, 8, 18, C.text);
  text(`Len ${e.length}`, 10, 34, 18, C.text);
  text(`${e.mode.toUpperCase()} · ${d.name}`, 130, 8, 18, C.text);
  text(`Speed ${e.speed}`, 130, 34, 18, C.text);
  const sc = e.aiStatus === AIStatus.SAFE_ROUTE ? C.head : e.aiStatus === AIStatus.SURVIVAL_WANDER ? C.accent : e.aiStatus === AIStatus.NO_PATH ? C.danger : C.text;
  text(e.hudStatus, 320, 8, 18, sc);
  text(`Pellets ${e.pellets}  Ticks ${e.ticks}`, 320, 36, 13, C.dim);
  // help line
  const hy = HUD_H + d.height * CELL;
  ctx.fillStyle = C.panel; ctx.fillRect(0, hy, canvas.width, HELP_H);
  text("Arrows/WASD move · P pause · +/- speed · T explored tint · R restart · Esc menu", 10, hy + 6, 13, C.dim);
}

function overlay(title, lines, color) {
  ctx.fillStyle = "rgba(0,0,0,0.72)"; ctx.fillRect(0, 0, canvas.width, canvas.height);
  const w = canvas.width, h = canvas.height;
  text(title, w / 2, h / 2 - 60, 44, color, "center");
  lines.forEach((l, i) => text(l, w / 2, h / 2 + i * 30, 18, C.text, "center"));
}

// ---------------------------------------------------------------- input
const KEYMAP = { ArrowUp: "UP", w: "UP", W: "UP", ArrowDown: "DOWN", s: "DOWN", S: "DOWN",
  ArrowLeft: "LEFT", a: "LEFT", A: "LEFT", ArrowRight: "RIGHT", d: "RIGHT", D: "RIGHT" };

document.addEventListener("keydown", (ev) => {
  const k = ev.key;
  if (["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"," "].includes(k)) ev.preventDefault();
  if (app.state === "menu") {
    if (k === "ArrowUp" || k === "w") app.menuIndex = (app.menuIndex + 2) % 3;
    else if (k === "ArrowDown" || k === "s") app.menuIndex = (app.menuIndex + 1) % 3;
    else if (k === "ArrowLeft") { app.diffIndex = (app.diffIndex + app.diffKeys.length - 1) % app.diffKeys.length; app.difficulty = DIFFICULTIES[app.diffKeys[app.diffIndex]]; resize(); }
    else if (k === "ArrowRight") { app.diffIndex = (app.diffIndex + 1) % app.diffKeys.length; app.difficulty = DIFFICULTIES[app.diffKeys[app.diffIndex]]; resize(); }
    else if (k === "Enter" || k === " ") {
      if (app.menuIndex === 0) { app.mode = "manual"; startRun(); }
      else if (app.menuIndex === 1) { app.mode = "ai"; startRun(); }
      else window.close();
    }
  } else if (app.state === "playing") {
    if (KEYMAP[k] && app.engine.mode === "manual") app.engine.queueDirection(KEYMAP[k]);
    else if (k === "p" || k === "P") app.state = "paused";
    else if (k === "+" || k === "=") app.engine.adjustSpeed(1);
    else if (k === "-") app.engine.adjustSpeed(-1);
    else if (k === "t" || k === "T") app.showExplored = !app.showExplored;
    else if (k === "r" || k === "R") startRun();
    else if (k === "Escape") { persistSettings(); app.state = "menu"; }
  } else if (app.state === "paused") {
    if (k === "p" || k === "P") app.state = "playing";
    else if (k === "Escape") { persistSettings(); app.state = "menu"; }
  } else if (app.state === "game_over") {
    if (k === "r" || k === "R") startRun();
    else if (k === "Escape") { persistSettings(); app.state = "menu"; }
  }
});

// ---------------------------------------------------------------- loop
function frame(now) {
  if (app.state === "menu") drawMenu();
  else if (app.state === "playing") {
    const e = app.engine;
    const interval = 1000 / e.speed;
    if (now - app.lastTick >= interval) {
      app.lastTick = now;
      e.tick();
      if (!e.alive || e.won) {
        app.newBest = store.saveBest(app.difficulty.name, e.mode, e.score);
        persistSettings();
        app.state = "game_over";
      }
    }
    drawPlay();
  } else if (app.state === "paused") {
    drawPlay();
    overlay("PAUSED", ["P resume · Esc menu"], C.accent);
  } else if (app.state === "game_over") {
    drawPlay();
    const e = app.engine;
    const title = e.won ? "BOARD FULL — YOU WIN" : "GAME OVER";
    const lines = [`Score ${e.score}   Best ${store.best(app.difficulty.name, e.mode)}${app.newBest ? "   NEW BEST!" : ""}`];
    if (e.mode === "ai") lines.push(`Pellets ${e.pellets} · Ticks survived ${e.ticks} · Fallbacks ${e.fallbackCount}`);
    lines.push("R restart · Esc menu");
    overlay(title, lines, e.won ? C.head : C.danger);
  }
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
