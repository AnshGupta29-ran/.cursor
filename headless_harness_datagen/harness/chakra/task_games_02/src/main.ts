// Rustwake: Core Rush — app controller.
// Screens: menu -> new skirmish setup -> match -> result. Canvas board,
// mouse-driven with Esc deselect / Enter end turn / P pause. Resume Match on
// reload restores the full state incl. RNG position.

import { MAPS, getMap } from './data/maps.js';
import {
  GameState,
  Unit,
  Vec,
  UNIT_STATS,
  TURN_CAP,
  tileAt,
} from './core/types.js';
import { Rng } from './core/rng.js';
import {
  createMatch,
  beginSideTurn,
  endTurn,
  applyMove,
  applyAttack,
  applyPickup,
  legalMoves,
  previewShot,
} from './core/game.js';
import { unitAt, isAdjacent } from './core/board.js';
import { decideWithWorker } from './worker/aiClient';
import { Telemetry, fetchMetrics } from './net/telemetry.js';
import {
  saveMatch,
  loadMatch,
  clearMatch,
  loadSettings,
  saveSettings,
  pushHistory,
  loadHistory,
} from './core/persist.js';
import { render, tileFromPixel, CANVAS_W, CANVAS_H, RenderOptions } from './ui/render.js';

type Screen = 'menu' | 'setup' | 'match' | 'result';

const telemetry = new Telemetry();

const app = document.getElementById('app')!;
let screen: Screen = 'menu';
let state: GameState | null = null;
let selected: Unit | null = null;
let moveHighlights = new Map<string, number>();
let reachableTargets = new Set<string>();
let hoverTile: Vec | null = null;
let shotPreview: ReturnType<typeof computePreview> = null;
let paused = false;
let aiBusy = false;
let resultInfo: { winner: string; turns: number; cause: string; seed: number } | null = null;
let setupMapId = MAPS[0].id;
let setupDifficulty: 'easy' | 'normal' = 'normal';
let canvas: HTMLCanvasElement | null = null;
let ctx: CanvasRenderingContext2D | null = null;

function computePreview(target: Unit) {
  if (!state || !selected) return null;
  const preview = previewShot(state, selected, target);
  return { target, preview };
}

// ---------------------------------------------------------------------------
// Screens
// ---------------------------------------------------------------------------

function showMenu(): void {
  screen = 'menu';
  const resume = loadMatch();
  const history = loadHistory();
  const settings = loadSettings();
  app.innerHTML = `
    <div class="screen">
      <h1>Rustwake</h1>
      <h2>Core Rush</h2>
      <p class="tagline">Two salvage crews. One power core. Drag it home or scrap the competition.</p>
      <div class="panel" style="text-align:center">
        <button id="btn-new">New Skirmish</button>
        ${resume ? `<button id="btn-resume" class="secondary">Resume Match (turn ${resume.turn}, seed ${resume.rng.seed})</button>` : ''}
      </div>
      <div class="panel" style="min-width:520px">
        <h2 style="margin-bottom:8px">Recent Salvage Runs</h2>
        <div id="history">
          ${
            history.length === 0
              ? '<p class="label">No matches yet. The junkyard waits.</p>'
              : history
                  .map(
                    (h) => `
              <div class="history-row">
                <span class="${h.winner === 'player' ? 'win' : h.winner === 'ai' ? 'loss' : 'draw'}">
                  ${h.winner === 'player' ? 'Copperjacks win' : h.winner === 'ai' ? 'Ferroscouts win' : 'Draw'}
                </span>
                <span>${h.mapId} · ${h.difficulty} · ${h.turns} turns</span>
                <span class="label">${new Date(h.ts).toLocaleDateString()}</span>
              </div>`,
                  )
                  .join('')
          }
        </div>
      </div>
      <div class="panel" style="min-width:520px">
        <label class="row" style="cursor:pointer">
          <input type="checkbox" id="opt-telemetry" ${settings.telemetryOptOut ? 'checked' : ''} />
          <span class="label">Opt out of telemetry (structured match logs to the local observability API)</span>
        </label>
        <div id="metrics-line" class="label" style="margin-top:6px"></div>
      </div>
    </div>`;

  document.getElementById('btn-new')!.onclick = showSetup;
  const resumeBtn = document.getElementById('btn-resume');
  if (resumeBtn && resume) {
    resumeBtn.onclick = () => {
      state = resume;
      telemetry.setMatch(state.matchId);
      telemetry.setTurn(state.turn);
      showMatch();
      if (state.active === 'ai') void runAi();
    };
  }
  document.getElementById('opt-telemetry')!.onchange = (e) => {
    const s = loadSettings();
    s.telemetryOptOut = (e.target as HTMLInputElement).checked;
    saveSettings(s);
  };
  void fetchMetrics().then((m) => {
    const el = document.getElementById('metrics-line');
    if (el) {
      el.textContent = m
        ? `Observability API online — matches started: ${m.matches_started}, completed: ${m.matches_completed}, log events: ${m.log_events_received}`
        : 'Observability API offline — logs will buffer locally.';
    }
  });
}

function showSetup(): void {
  screen = 'setup';
  app.innerHTML = `
    <div class="screen">
      <h1 style="font-size:24px">New Skirmish</h1>
      <div class="panel" style="min-width:520px">
        <h2 style="margin-bottom:8px">Junkyard Layout</h2>
        ${MAPS.map(
          (m) => `
          <div class="map-card ${m.id === setupMapId ? 'selected' : ''}" data-map="${m.id}">
            <span>${m.name}</span><span class="label">${m.id}</span>
          </div>`,
        ).join('')}
      </div>
      <div class="panel" style="min-width:520px">
        <h2 style="margin-bottom:8px">Scrapbrain Difficulty</h2>
        <div class="map-card ${setupDifficulty === 'easy' ? 'selected' : ''}" data-diff="easy">
          <span>Easy</span><span class="label">15% blunder rate — picks second-best moves</span>
        </div>
        <div class="map-card ${setupDifficulty === 'normal' ? 'selected' : ''}" data-diff="normal">
          <span>Normal</span><span class="label">Full utility scoring</span>
        </div>
      </div>
      <div>
        <button id="btn-start">Deploy Crews</button>
        <button id="btn-back" class="secondary">Back</button>
      </div>
    </div>`;

  for (const el of app.querySelectorAll('[data-map]')) {
    (el as HTMLElement).onclick = () => {
      setupMapId = (el as HTMLElement).dataset.map!;
      showSetup();
    };
  }
  for (const el of app.querySelectorAll('[data-diff]')) {
    (el as HTMLElement).onclick = () => {
      setupDifficulty = (el as HTMLElement).dataset.diff as 'easy' | 'normal';
      showSetup();
    };
  }
  document.getElementById('btn-back')!.onclick = showMenu;
  document.getElementById('btn-start')!.onclick = startMatch;
}

function startMatch(): void {
  const map = getMap(setupMapId);
  const seed = (Math.random() * 0xffffffff) >>> 0;
  state = createMatch(map, seed, setupDifficulty);
  telemetry.setMatch(state.matchId);
  telemetry.setTurn(state.turn);
  telemetry.sink({ type: 'match_start', data: { mapId: map.id, difficulty: setupDifficulty, seed } });
  beginSideTurn(state);
  saveMatch(state);
  showMatch();
}

function showMatch(): void {
  screen = 'match';
  selected = null;
  moveHighlights = new Map();
  reachableTargets = new Set();
  shotPreview = null;
  paused = false;
  app.innerHTML = `
    <div class="screen">
      <div id="hud">
        <span id="banner"></span>
        <span class="label" id="seedline"></span>
        <span>
          <button id="btn-endturn" title="Enter">End Turn</button>
          <button id="btn-quit" class="secondary">Menu</button>
        </span>
      </div>
      <canvas id="board" width="${CANVAS_W}" height="${CANVAS_H}"></canvas>
      <div id="logstrip"></div>
      <div class="label" style="width:960px">
        Click a Copperjack to select · click blue tile to move (1 AP) · click a Ferroscout to shoot (1 AP, ends unit) ·
        click the core-adjacent prompt to grab · <b>Esc</b> deselect · <b>Enter</b> end turn · <b>P</b> pause
      </div>
    </div>`;
  canvas = document.getElementById('board') as HTMLCanvasElement;
  ctx = canvas.getContext('2d')!;
  canvas.addEventListener('click', onBoardClick);
  canvas.addEventListener('mousemove', onBoardHover);
  document.getElementById('btn-endturn')!.onclick = playerEndTurn;
  document.getElementById('btn-quit')!.onclick = () => {
    if (state && !state.over) saveMatch(state);
    showMenu();
  };
  window.onkeydown = onKey;
  maybeShowControlsOverlay();
  redraw();
}

function showResult(): void {
  if (!state) return;
  screen = 'result';
  clearMatch();
  resultInfo = {
    winner: state.winner ?? 'draw',
    turns: state.turn,
    cause: state.endCause ?? '',
    seed: state.rng.seed,
  };
  pushHistory({
    matchId: state.matchId,
    mapId: state.mapId,
    difficulty: state.difficulty,
    winner: state.winner ?? 'draw',
    turns: state.turn,
    cause: state.endCause ?? '',
    seed: state.rng.seed,
    ts: Date.now(),
  });
  void telemetry.flush();

  const w = resultInfo.winner;
  const headline =
    w === 'player' ? 'Copperjacks haul it home!' : w === 'ai' ? 'Ferroscouts take the core' : 'Dead even in the dust';
  app.innerHTML = `
    <div class="screen">
      <h1 style="font-size:26px">${headline}</h1>
      <div class="panel" style="text-align:center; min-width:440px">
        <p>${resultInfo.cause}</p>
        <p class="label">Turns: ${resultInfo.turns} / ${TURN_CAP}</p>
        <p class="label">Match seed: ${resultInfo.seed} (deterministic combat stream)</p>
      </div>
      <div>
        <button id="btn-again">Play Again</button>
        <button id="btn-menu" class="secondary">Menu</button>
      </div>
    </div>`;
  document.getElementById('btn-again')!.onclick = showSetup;
  document.getElementById('btn-menu')!.onclick = showMenu;
  window.onkeydown = null;
}

// ---------------------------------------------------------------------------
// Match interaction
// ---------------------------------------------------------------------------

function refreshSelection(): void {
  moveHighlights = new Map();
  reachableTargets = new Set();
  shotPreview = null;
  if (state && selected && selected.alive && state.active === 'player' && !selected.acted) {
    moveHighlights = legalMoves(state, selected);
    if (selected.ap >= 1) {
      for (const u of state.units) {
        if (u.alive && u.team === 'ai') {
          const p = previewShot(state, selected, u);
          if (p.canShoot) reachableTargets.add(u.id);
        }
      }
    }
  }
}

function redraw(): void {
  if (!ctx || !state || screen !== 'match') return;
  const banner = document.getElementById('banner');
  const seedline = document.getElementById('seedline');
  if (banner) {
    banner.textContent = state.over
      ? 'Match over'
      : state.active === 'player'
        ? `Turn ${state.turn} — Copperjacks (you)`
        : `Turn ${state.turn} — Ferroscouts thinking…`;
    banner.style.color = state.active === 'player' ? 'var(--copper)' : 'var(--teal)';
  }
  if (seedline) seedline.textContent = `map ${state.mapId} · ${state.difficulty} · seed ${state.rng.seed}`;
  const opts: RenderOptions = {
    selected,
    moveHighlights,
    hoverTile,
    shotPreview,
    reachableTargets,
    paused,
  };
  render(ctx, state, opts);
  const strip = document.getElementById('logstrip');
  if (strip) strip.textContent = telemetry.strip.join('\n');
}

function onBoardHover(e: MouseEvent): void {
  if (!canvas || !state || paused) return;
  const rect = canvas.getBoundingClientRect();
  const tile = tileFromPixel(e.clientX - rect.left, e.clientY - rect.top);
  hoverTile = tile;
  shotPreview = null;
  if (tile && selected) {
    const u = unitAt(state, tile.x, tile.y);
    if (u && u.team === 'ai') shotPreview = computePreview(u);
  }
  redraw();
}

function onBoardClick(e: MouseEvent): void {
  if (!canvas || !state || state.over || paused || aiBusy) return;
  if (state.active !== 'player') return;
  const rect = canvas.getBoundingClientRect();
  const tile = tileFromPixel(e.clientX - rect.left, e.clientY - rect.top);
  if (!tile) return;
  const rng = new Rng(state.rng);

  const clicked = unitAt(state, tile.x, tile.y);

  // Attack an enemy.
  if (selected && clicked && clicked.team === 'ai') {
    if (applyAttack(state, rng, selected, clicked, telemetry.sink)) {
      state.rng = rng.state();
      afterAction();
      return;
    }
  }

  // Select own unit.
  if (clicked && clicked.team === 'player' && clicked.alive) {
    selected = clicked;
    refreshSelection();
    redraw();
    return;
  }

  if (selected) {
    // Pick up the core (click the core tile while adjacent or on it).
    if (
      state.core.pos &&
      tile.x === state.core.pos.x &&
      tile.y === state.core.pos.y &&
      (isAdjacent(selected.pos, state.core.pos) ||
        (selected.pos.x === state.core.pos.x && selected.pos.y === state.core.pos.y))
    ) {
      if (applyPickup(state, selected, telemetry.sink)) {
        afterAction();
        return;
      }
    }
    // Move.
    if (applyMove(state, selected, tile, telemetry.sink)) {
      afterAction();
      return;
    }
  }
  refreshSelection();
  redraw();
}

function afterAction(): void {
  if (!state) return;
  saveMatch(state);
  if (state.over) {
    redraw();
    setTimeout(showResult, 600);
    return;
  }
  refreshSelection();
  redraw();
}

function playerEndTurn(): void {
  if (!state || state.over || state.active !== 'player' || aiBusy || paused) return;
  selected = null;
  refreshSelection();
  endTurn(state, telemetry.sink);
  telemetry.setTurn(state.turn);
  saveMatch(state);
  redraw();
  if (state.over) {
    setTimeout(showResult, 600);
    return;
  }
  void runAi();
}

async function runAi(): Promise<void> {
  if (!state || state.over) return;
  aiBusy = true;
  redraw();
  try {
    const units = state.units.filter((u) => u.alive && u.team === 'ai');
    for (const unit of units) {
      let guard = 8;
      while (state && !state.over && unit.alive && unit.ap > 0 && !unit.acted && guard-- > 0) {
        const before = `${unit.pos.x},${unit.pos.y},${unit.ap}`;
        const decision = await decideWithWorker(state, unit, state.rng);
        state.rng = decision.rng;
        const rng = new Rng(state.rng);
        const act = decision.action;
        const u = state.units.find((x) => x.id === act.unitId);
        if (u && u.alive) {
          if (act.kind === 'attack') {
            const t = state.units.find((x) => x.id === act.targetId);
            if (t) {
              if (act.moveTo) applyMove(state, u, act.moveTo, telemetry.sink);
              applyAttack(state, rng, u, t, telemetry.sink);
            } else {
              u.acted = true;
              u.ap = 0;
            }
          } else if (act.kind === 'move') {
            applyMove(state, u, act.to, telemetry.sink);
          } else if (act.kind === 'pickup') {
            applyPickup(state, u, telemetry.sink);
          } else {
            u.acted = true;
            u.ap = 0;
          }
        }
        state.rng = rng.state();
        redraw();
        await new Promise((r) => setTimeout(r, 220)); // readable pacing
        const after = `${unit.pos.x},${unit.pos.y},${unit.ap}`;
        if (before === after) {
          unit.ap = 0;
          unit.acted = true;
        }
      }
      if (!state || state.over) break;
    }
  } finally {
    aiBusy = false;
  }
  if (!state) return;
  saveMatch(state);
  if (state.over) {
    redraw();
    setTimeout(showResult, 600);
    return;
  }
  endTurn(state, telemetry.sink);
  telemetry.setTurn(state.turn);
  saveMatch(state);
  redraw();
  if (state.over) setTimeout(showResult, 600);
}

function onKey(e: KeyboardEvent): void {
  if (screen !== 'match') return;
  if (e.key === 'Escape') {
    selected = null;
    refreshSelection();
    redraw();
  } else if (e.key === 'Enter') {
    playerEndTurn();
  } else if (e.key === 'p' || e.key === 'P') {
    paused = !paused;
    redraw();
  }
}

function maybeShowControlsOverlay(): void {
  const settings = loadSettings();
  if (settings.seenControls) return;
  const overlay = document.createElement('div');
  overlay.id = 'overlay';
  overlay.innerHTML = `
    <div class="panel">
      <h2 style="margin-bottom:10px">How to play</h2>
      <p>The hauler's power core sits mid-yard. <b>Grab it and carry it to your extraction row</b>
      (bottom, copper) — or just <b>scrap all three Ferroscouts</b>.</p>
      <p>
        <kbd>Click</kbd> unit to select · <kbd>Click</kbd> blue tile to move (1 AP)<br/>
        <kbd>Click</kbd> enemy to shoot — the dashed preview shows hit % and cover<br/>
        <kbd>Click</kbd> the core tile while adjacent to grab it (1 AP)<br/>
        <kbd>Esc</kbd> deselect · <kbd>Enter</kbd> end turn · <kbd>P</kbd> pause
      </p>
      <p class="label">Each unit gets 2 AP per turn. Crates halve your odds (80%→55%);
      containers block shots entirely. Spotters ignore crates. Turn cap ${TURN_CAP}.</p>
      <button id="btn-gotit" style="width:100%">To the junkyard</button>
    </div>`;
  document.body.appendChild(overlay);
  document.getElementById('btn-gotit')!.onclick = () => {
    settings.seenControls = true;
    saveSettings(settings);
    overlay.remove();
  };
}

// Boot.
showMenu();
