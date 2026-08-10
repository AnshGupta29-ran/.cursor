// Game-state engine: match construction, legal actions, applying moves/
// attacks/pickups, turn flow. Emits log events through a callback. Pure with
// respect to IO (no DOM, no fetch) so tests, smoke, worker and UI all share it.

import { Rng } from './rng.js';
import { MapDef, UNIT_STATS, BOARD_H, BOARD_W } from './types.js';
import type {
  BoardState,
  GameState,
  LogEvent,
  Team,
  TileKind,
  Unit,
  Vec,
} from './types.js';
import { isAdjacent, movementRange, nearestOpenAdjacent, unitAt } from './board.js';
import { previewShot, resolveAttack } from './combat.js';
import { checkWin } from './win.js';

export type LogSink = (e: Omit<LogEvent, 'sessionId' | 'matchId' | 'turn' | 'ts'>) => void;

let matchCounter = 0;

export function newMatchId(): string {
  matchCounter++;
  return `m_${Date.now().toString(36)}_${matchCounter}`;
}

/** Build a fresh match from a map definition. */
export function createMatch(
  map: MapDef,
  seed: number,
  difficulty: 'easy' | 'normal',
  matchId: string = newMatchId(),
): GameState {
  const tiles: TileKind[] = [];
  for (let y = 0; y < BOARD_H; y++) {
    for (let x = 0; x < BOARD_W; x++) {
      const ch = map.rows[y][x];
      tiles.push(ch === 'c' ? 'crate' : ch === '#' ? 'container' : ch === 'X' ? 'corespawn' : 'open');
    }
  }
  const board: BoardState = {
    w: BOARD_W,
    h: BOARD_H,
    tiles,
    extractionRow: { player: BOARD_H - 1, ai: 0 },
  };
  const units: Unit[] = [];
  let n = 0;
  for (const team of ['player', 'ai'] as Team[]) {
    for (const s of map.spawns[team]) {
      const stats = UNIT_STATS[s.cls];
      units.push({
        id: `${team[0]}${n++}`,
        team,
        cls: s.cls,
        pos: { x: s.x, y: s.y },
        hp: stats.hp,
        maxHp: stats.hp,
        ap: 2,
        acted: false,
        alive: true,
        hasCore: false,
      });
    }
  }
  // Core spawns at the center-most 'X' tile.
  let corePos: Vec = { x: (BOARD_W / 2) | 0, y: (BOARD_H / 2) | 0 };
  outer: for (let y = 0; y < BOARD_H; y++) {
    for (let x = 0; x < BOARD_W; x++) {
      if (map.rows[y][x] === 'X') {
        corePos = { x, y };
        break outer;
      }
    }
  }
  return {
    board,
    units,
    core: { pos: corePos, carrierId: null },
    active: 'player',
    turn: 1,
    rng: { seed, calls: 0 },
    mapId: map.id,
    difficulty,
    over: false,
    winner: null,
    endCause: null,
    matchId,
  };
}

/** Begin a side's activation: reset AP for that side's living units. */
export function beginSideTurn(state: GameState): void {
  for (const u of state.units) {
    if (u.team === state.active && u.alive) {
      u.ap = 2;
      u.acted = false;
    }
  }
}

/** End the active side's turn; flip sides, advance turn counter, check cap. */
export function endTurn(state: GameState, log?: LogSink): void {
  if (state.over) return;
  state.active = state.active === 'player' ? 'ai' : 'player';
  if (state.active === 'player') state.turn += 1;
  beginSideTurn(state);
  log?.({ type: 'turn_start', data: { side: state.active, turn: state.turn } });
  applyWin(state, log);
}

/** Legal move destinations for a unit (must have AP and not have attacked). */
export function legalMoves(state: GameState, unit: Unit): Map<string, number> {
  if (!unit.alive || unit.ap < 1 || unit.acted) return new Map();
  return movementRange(state, unit.pos, UNIT_STATS[unit.cls].move, unit.id);
}

export function canAct(state: GameState, unit: Unit): boolean {
  return state.active === unit.team && unit.alive && !state.over;
}

/** Move a unit to an adjacent-or-reachable tile; costs 1 AP. */
export function applyMove(state: GameState, unit: Unit, to: Vec, log?: LogSink): boolean {
  if (!canAct(state, unit) || unit.ap < 1 || unit.acted) return false;
  const range = legalMoves(state, unit);
  if (!range.has(`${to.x},${to.y}`)) return false;
  unit.pos = { ...to };
  unit.ap -= 1;
  log?.({ type: 'move', data: { unit: unit.id, cls: unit.cls, team: unit.team, x: to.x, y: to.y } });
  applyWin(state, log); // carrier stepping onto home row wins immediately
  return true;
}

/** Attack a target; costs 1 AP and ends the unit's activation. */
export function applyAttack(
  state: GameState,
  rng: Rng,
  attacker: Unit,
  target: Unit,
  log?: LogSink,
): boolean {
  if (!canAct(state, attacker) || attacker.ap < 1 || attacker.acted) return false;
  const preview = previewShot(state, attacker, target);
  if (!preview.canShoot) return false;
  log?.({
    type: 'attack',
    data: {
      attacker: attacker.id,
      target: target.id,
      chance: preview.chance,
      halfCover: preview.halfCover,
    },
  });
  const out = resolveAttack(state, rng, attacker, target);
  attacker.ap -= 1;
  attacker.acted = true;
  if (out.hit) {
    log?.({ type: 'hit', data: { attacker: attacker.id, target: target.id, dmg: out.dmg, hpLeft: target.hp } });
  } else {
    log?.({ type: 'miss', data: { attacker: attacker.id, target: target.id } });
  }
  if (out.targetDown) {
    log?.({ type: 'unit_down', data: { unit: target.id, cls: target.cls, team: target.team } });
    dropCore(state, target, log);
  }
  applyWin(state, log);
  return true;
}

/** Pick up the core: unit must be adjacent to the core tile; costs 1 AP. */
export function applyPickup(state: GameState, unit: Unit, log?: LogSink): boolean {
  if (!canAct(state, unit) || unit.ap < 1 || unit.acted) return false;
  if (!state.core.pos || state.core.carrierId) return false;
  if (!isAdjacent(unit.pos, state.core.pos) &&
      !(unit.pos.x === state.core.pos.x && unit.pos.y === state.core.pos.y)) {
    return false;
  }
  state.core.carrierId = unit.id;
  state.core.pos = null;
  unit.hasCore = true;
  unit.ap -= 1;
  log?.({ type: 'core_pickup', data: { unit: unit.id, team: unit.team } });
  applyWin(state, log);
  return true;
}

/** Drop the core when its carrier goes down. */
export function dropCore(state: GameState, carrier: Unit, log?: LogSink): void {
  if (!carrier.hasCore) return;
  carrier.hasCore = false;
  state.core.carrierId = null;
  const spot = nearestOpenAdjacent(state, carrier.pos);
  state.core.pos = spot ?? { ...carrier.pos };
  log?.({ type: 'core_drop', data: { x: state.core.pos.x, y: state.core.pos.y, from: carrier.id } });
}

/** Evaluate win conditions and stamp the state when over. */
export function applyWin(state: GameState, log?: LogSink): void {
  if (state.over) return;
  const w = checkWin(state);
  if (w.over) {
    state.over = true;
    state.winner = w.winner;
    state.endCause = w.cause;
    log?.({
      type: 'match_end',
      data: { winner: w.winner, cause: w.cause, turns: state.turn },
    });
  }
}

export function aliveUnits(state: GameState, team: Team): Unit[] {
  return state.units.filter((u) => u.alive && u.team === team);
}

export function enemiesOf(state: GameState, team: Team): Unit[] {
  return state.units.filter((u) => u.alive && u.team !== team);
}

export { previewShot, unitAt };
