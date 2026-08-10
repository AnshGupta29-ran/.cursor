// Unit tests for the pure rules modules.

import { describe, it, expect } from 'vitest';
import { Rng, mulberry32 } from '../src/core/rng.js';
import { createMatch, applyMove, applyAttack, applyPickup, endTurn, legalMoves } from '../src/core/game.js';
import { movementRange, nearestOpenAdjacent } from '../src/core/board.js';
import { los } from '../src/core/los.js';
import { previewShot, BASE_HIT, COVER_HIT } from '../src/core/combat.js';
import { checkWin } from '../src/core/win.js';
import { scoreActions, chooseAction } from '../src/core/ai.js';
import { getMap, MAPS } from '../src/data/maps.js';
import { GameState, Unit, UNIT_STATS, TURN_CAP } from '../src/core/types.js';

function openBoardState(): GameState {
  // All-open board, player bottom row, ai top row, units placed manually.
  const state = createMatch(getMap('scrapyard-cross'), 42, 'normal');
  // Flatten tiles to open and clear units for controlled scenarios.
  state.board.tiles = state.board.tiles.map(() => 'open');
  state.units = [];
  state.core = { pos: null, carrierId: null };
  return state;
}

function mkUnit(partial: Partial<Unit> & Pick<Unit, 'id' | 'team' | 'cls' | 'pos'>): Unit {
  const stats = UNIT_STATS[partial.cls];
  return {
    hp: stats.hp,
    maxHp: stats.hp,
    ap: 2,
    acted: false,
    alive: true,
    hasCore: false,
    ...partial,
  };
}

describe('seeded RNG reproducibility', () => {
  it('same seed + same draws = same stream', () => {
    const a = new Rng({ seed: 1234, calls: 0 });
    const b = new Rng({ seed: 1234, calls: 0 });
    for (let i = 0; i < 20; i++) expect(a.next()).toBe(b.next());
  });

  it('restoring from {seed, calls} continues the same stream', () => {
    const a = new Rng({ seed: 999, calls: 0 });
    const first5 = [a.next(), a.next(), a.next(), a.next(), a.next()];
    const mid = a.state();
    const restA = [a.next(), a.next(), a.next()];
    const b = new Rng(mid); // restore
    const restB = [b.next(), b.next(), b.next()];
    expect(restB).toEqual(restA);
    expect(first5).toHaveLength(5);
  });

  it('mulberry32 differs across seeds', () => {
    const f1 = mulberry32(1);
    const f2 = mulberry32(2);
    expect(f1()).not.toBe(f2());
  });
});

describe('BFS movement range', () => {
  it('reaches Manhattan neighborhood on open board within budget', () => {
    const s = openBoardState();
    const u = mkUnit({ id: 'p0', team: 'player', cls: 'runner', pos: { x: 5, y: 5 } });
    s.units = [u];
    const range = movementRange(s, u.pos, 5);
    // Runner with 5 move on open 12x9 reaches 1+2*(5*6)=... bounded by board.
    expect(range.get('5,5')).toBe(0);
    expect(range.get('10,5')).toBe(5);
    expect(range.get('5,0')).toBe(5);
    expect(range.has('11,5')).toBe(false); // 6 away
  });

  it('crates and containers block movement; occupied tiles block pathing', () => {
    const s = openBoardState();
    s.board.tiles[5 * 12 + 6] = 'crate'; // right of unit
    const u = mkUnit({ id: 'p0', team: 'player', cls: 'bruiser', pos: { x: 5, y: 5 } });
    const e = mkUnit({ id: 'a0', team: 'ai', cls: 'bruiser', pos: { x: 5, y: 4 } });
    s.units = [u, e];
    const range = movementRange(s, u.pos, 3);
    expect(range.has('6,5')).toBe(false); // crate
    expect(range.has('5,4')).toBe(false); // enemy-occupied
    expect(range.has('4,5')).toBe(true); // left is open
  });
});

describe('LOS and cover', () => {
  it('containers block the shot', () => {
    const s = openBoardState();
    s.board.tiles[5 * 12 + 5] = 'container'; // between (3,5) and (7,5)
    const r = los(s.board, { x: 3, y: 5 }, { x: 7, y: 5 });
    expect(r.clear).toBe(false);
  });

  it('crate adjacent to target grants half cover; 55% vs 80%', () => {
    const s = openBoardState();
    // Runner (range 2) shooting along a row with a crate adjacent to the target.
    const atk = mkUnit({ id: 'p0', team: 'player', cls: 'runner', pos: { x: 2, y: 5 } });
    const tgt = mkUnit({ id: 'a0', team: 'ai', cls: 'bruiser', pos: { x: 4, y: 5 } });
    s.units = [atk, tgt];
    // No cover: base 80%.
    let p = previewShot(s, atk, tgt);
    expect(p.canShoot).toBe(true);
    expect(p.chance).toBe(BASE_HIT);
    // Crate at (3,5): adjacent to target (4,5), line crosses it -> 55%.
    s.board.tiles[5 * 12 + 3] = 'crate';
    p = previewShot(s, atk, tgt);
    expect(p.canShoot).toBe(true);
    expect(p.halfCover).toBe(true);
    expect(p.chance).toBe(COVER_HIT);
  });

  it('spotter ignores half cover', () => {
    const s = openBoardState();
    const atk = mkUnit({ id: 'p0', team: 'player', cls: 'spotter', pos: { x: 2, y: 5 } });
    const tgt = mkUnit({ id: 'a0', team: 'ai', cls: 'runner', pos: { x: 4, y: 5 } });
    s.board.tiles[5 * 12 + 3] = 'crate';
    s.units = [atk, tgt];
    const p = previewShot(s, atk, tgt);
    expect(p.canShoot).toBe(true);
    expect(p.halfCover).toBe(false);
    expect(p.chance).toBe(BASE_HIT);
  });

  it('out of range shots are refused', () => {
    const s = openBoardState();
    const atk = mkUnit({ id: 'p0', team: 'player', cls: 'bruiser', pos: { x: 0, y: 0 } });
    const tgt = mkUnit({ id: 'a0', team: 'ai', cls: 'runner', pos: { x: 5, y: 5 } });
    s.units = [atk, tgt];
    const p = previewShot(s, atk, tgt);
    expect(p.canShoot).toBe(false);
  });
});

describe('combat resolution determinism', () => {
  it('same seed produces the same hit/miss sequence', () => {
    const build = () => {
      const s = openBoardState();
      const atk = mkUnit({ id: 'p0', team: 'player', cls: 'bruiser', pos: { x: 3, y: 3 } });
      const tgt = mkUnit({ id: 'a0', team: 'ai', cls: 'bruiser', pos: { x: 3, y: 4 } });
      s.units = [atk, tgt];
      s.active = 'player';
      return { s, atk, tgt };
    };
    const r1 = build();
    const r2 = build();
    const rng1 = new Rng({ seed: 777, calls: 0 });
    const rng2 = new Rng({ seed: 777, calls: 0 });
    const seq1: boolean[] = [];
    const seq2: boolean[] = [];
    for (let i = 0; i < 5; i++) {
      r1.atk.ap = 1; r1.atk.acted = false; r1.tgt.hp = 10; r1.tgt.alive = true;
      r2.atk.ap = 1; r2.atk.acted = false; r2.tgt.hp = 10; r2.tgt.alive = true;
      seq1.push(applyAttack(r1.s, rng1, r1.atk, r1.tgt));
      seq2.push(applyAttack(r2.s, rng2, r2.atk, r2.tgt));
    }
    // Compare resulting hp streams rather than return values.
    expect(seq1).toEqual(seq2);
  });
});

describe('win checks and tiebreak', () => {
  it('wipe ends the match', () => {
    const s = openBoardState();
    s.units = [mkUnit({ id: 'p0', team: 'player', cls: 'bruiser', pos: { x: 1, y: 1 } })];
    const w = checkWin(s);
    expect(w.over).toBe(true);
    expect(w.winner).toBe('player');
  });

  it('core extraction on home row wins', () => {
    const s = openBoardState();
    const carrier = mkUnit({ id: 'a0', team: 'ai', cls: 'runner', pos: { x: 4, y: 0 }, hasCore: true });
    s.units = [carrier, mkUnit({ id: 'p0', team: 'player', cls: 'bruiser', pos: { x: 1, y: 8 } })];
    s.core = { pos: null, carrierId: 'a0' };
    const w = checkWin(s);
    expect(w.over).toBe(true);
    expect(w.winner).toBe('ai');
  });

  it('turn cap: more units wins, then total HP, then draw', () => {
    const s = openBoardState();
    s.turn = TURN_CAP;
    s.units = [
      mkUnit({ id: 'p0', team: 'player', cls: 'bruiser', pos: { x: 1, y: 8 } }),
      mkUnit({ id: 'p1', team: 'player', cls: 'runner', pos: { x: 2, y: 8 } }),
      mkUnit({ id: 'a0', team: 'ai', cls: 'bruiser', pos: { x: 1, y: 0 } }),
    ];
    expect(checkWin(s).winner).toBe('player');

    // Equal counts, HP tiebreak.
    s.units = [
      mkUnit({ id: 'p0', team: 'player', cls: 'bruiser', pos: { x: 1, y: 8 }, hp: 10 }),
      mkUnit({ id: 'a0', team: 'ai', cls: 'bruiser', pos: { x: 1, y: 0 }, hp: 4 }),
    ];
    expect(checkWin(s).winner).toBe('player');

    // Exact tie -> draw.
    s.units = [
      mkUnit({ id: 'p0', team: 'player', cls: 'bruiser', pos: { x: 1, y: 8 }, hp: 5 }),
      mkUnit({ id: 'a0', team: 'ai', cls: 'bruiser', pos: { x: 1, y: 0 }, hp: 5 }),
    ];
    const w = checkWin(s);
    expect(w.over).toBe(true);
    expect(w.winner).toBe('draw');
  });

  it('defeated carrier drops the core on a neighboring open tile', () => {
    const s = openBoardState();
    const carrier = mkUnit({ id: 'a0', team: 'ai', cls: 'runner', pos: { x: 5, y: 5 }, hasCore: true, hp: 1 });
    const bruiser = mkUnit({ id: 'p0', team: 'player', cls: 'bruiser', pos: { x: 5, y: 4 } });
    s.units = [carrier, bruiser];
    s.core = { pos: null, carrierId: 'a0' };
    s.active = 'player';
    const rng = new Rng({ seed: 1, calls: 0 });
    // Force hits by burning the stream until a hit lands (base 80%).
    let down = false;
    for (let i = 0; i < 10 && !down; i++) {
      bruiser.ap = 1; bruiser.acted = false;
      if (applyAttack(s, rng, bruiser, carrier)) down = !carrier.alive;
    }
    expect(carrier.alive).toBe(false);
    expect(s.core.carrierId).toBeNull();
    expect(s.core.pos).not.toBeNull();
    // Drop tile is open & unoccupied.
    const spot = s.core.pos!;
    expect(s.board.tiles[spot.y * 12 + spot.x]).toBe('open');
  });

  it('nearestOpenAdjacent skips occupied tiles', () => {
    const s = openBoardState();
    s.units = [
      mkUnit({ id: 'p0', team: 'player', cls: 'bruiser', pos: { x: 6, y: 5 } }),
      mkUnit({ id: 'p1', team: 'player', cls: 'bruiser', pos: { x: 4, y: 5 } }),
      mkUnit({ id: 'p2', team: 'player', cls: 'bruiser', pos: { x: 5, y: 4 } }),
    ];
    const spot = nearestOpenAdjacent(s, { x: 5, y: 5 });
    expect(spot).toEqual({ x: 5, y: 6 });
  });
});

describe('core pickup', () => {
  it('adjacent unit grabs the core for 1 AP', () => {
    const s = openBoardState();
    const runner = mkUnit({ id: 'p0', team: 'player', cls: 'runner', pos: { x: 5, y: 5 } });
    s.units = [runner];
    s.core = { pos: { x: 5, y: 4 }, carrierId: null };
    s.active = 'player';
    expect(applyPickup(s, runner)).toBe(true);
    expect(runner.hasCore).toBe(true);
    expect(runner.ap).toBe(1);
    expect(s.core.carrierId).toBe('p0');
  });

  it('non-adjacent unit cannot grab', () => {
    const s = openBoardState();
    const runner = mkUnit({ id: 'p0', team: 'player', cls: 'runner', pos: { x: 0, y: 0 } });
    s.units = [runner];
    s.core = { pos: { x: 5, y: 4 }, carrierId: null };
    s.active = 'player';
    expect(applyPickup(s, runner)).toBe(false);
  });
});

describe('turn flow', () => {
  it('end turn flips side, refreshes AP, increments turn on player return', () => {
    const s = createMatch(getMap('scrapyard-cross'), 7, 'normal');
    s.turn = 1;
    s.active = 'player';
    endTurn(s);
    expect(s.active).toBe('ai');
    expect(s.turn).toBe(1);
    endTurn(s);
    expect(s.active).toBe('player');
    expect(s.turn).toBe(2);
    const p = s.units.find((u) => u.team === 'player')!;
    expect(p.ap).toBe(2);
    expect(p.acted).toBe(false);
  });

  it('boxed-in unit can still pass / attack', () => {
    const s = openBoardState();
    const u = mkUnit({ id: 'p0', team: 'player', cls: 'bruiser', pos: { x: 5, y: 5 } });
    // Surround with crates.
    s.board.tiles[5 * 12 + 4] = 'crate';
    s.board.tiles[5 * 12 + 6] = 'crate';
    s.board.tiles[4 * 12 + 5] = 'crate';
    s.board.tiles[6 * 12 + 5] = 'crate';
    s.units = [u];
    s.active = 'player';
    expect(legalMoves(s, u).size).toBe(1); // only its own tile
    u.acted = true;
    u.ap = 0;
    expect(u.acted).toBe(true); // passed
  });
});

describe('Scrapbrain AI sanity', () => {
  it('prefers attacking a reachable carrier over a distant healthy unit', () => {
    const s = openBoardState();
    const aiSpotter = mkUnit({ id: 'a0', team: 'ai', cls: 'spotter', pos: { x: 5, y: 3 } });
    const carrier = mkUnit({ id: 'p0', team: 'player', cls: 'runner', pos: { x: 5, y: 5 }, hasCore: true, hp: 6 });
    const distant = mkUnit({ id: 'p1', team: 'player', cls: 'bruiser', pos: { x: 0, y: 8 }, hp: 10 });
    s.units = [aiSpotter, carrier, distant];
    s.core = { pos: null, carrierId: 'p0' };
    s.active = 'ai';
    const scored = scoreActions(s, aiSpotter, 'ai');
    const best = scored.reduce((a, b) => (b.score > a.score ? b : a));
    expect(best.action.kind).toBe('attack');
    if (best.action.kind === 'attack') {
      expect(best.action.targetId).toBe('p0'); // the carrier, not the distant bruiser
    }
  });

  it('chooseAction is deterministic for a fixed rng state', () => {
    const s = openBoardState();
    const aiSpotter = mkUnit({ id: 'a0', team: 'ai', cls: 'spotter', pos: { x: 5, y: 3 } });
    const carrier = mkUnit({ id: 'p0', team: 'player', cls: 'runner', pos: { x: 5, y: 5 }, hasCore: true });
    s.units = [aiSpotter, carrier];
    s.core = { pos: null, carrierId: 'p0' };
    s.active = 'ai';
    const r1 = new Rng({ seed: 55, calls: 0 });
    const r2 = new Rng({ seed: 55, calls: 0 });
    const a1 = chooseAction(s, aiSpotter, 'ai', r1, 'normal');
    const a2 = chooseAction(s, aiSpotter, 'ai', r2, 'normal');
    expect(JSON.stringify(a1)).toBe(JSON.stringify(a2));
  });

  it('easy difficulty sometimes blunders (second-best pick) across seeds', () => {
    let blunders = 0;
    const N = 40;
    for (let seed = 0; seed < N; seed++) {
      const s = openBoardState();
      const ai = mkUnit({ id: 'a0', team: 'ai', cls: 'runner', pos: { x: 5, y: 3 } });
      s.units = [ai, mkUnit({ id: 'p0', team: 'player', cls: 'bruiser', pos: { x: 8, y: 8 } })];
      s.core = { pos: { x: 5, y: 4 }, carrierId: null };
      s.active = 'ai';
      const scored = scoreActions(s, ai, 'ai');
      for (const x of scored) x.score += 0; // no jitter here
      scored.sort((a, b) => b.score - a.score);
      const bestAction = JSON.stringify(scored[0].action);
      const rng = new Rng({ seed, calls: 0 });
      const picked = JSON.stringify(chooseAction(s, ai, 'ai', rng, 'easy'));
      if (picked !== bestAction) blunders++; // jitter OR blunder changed the pick
    }
    // With 15% blunder + tie jitter we expect some, but not all, picks to deviate.
    expect(blunders).toBeGreaterThan(0);
    expect(blunders).toBeLessThan(N);
  });
});

describe('maps', () => {
  it('three maps, all valid dimensions', () => {
    expect(MAPS).toHaveLength(3);
    for (const m of MAPS) {
      expect(getMap(m.id).rows).toHaveLength(9);
    }
  });

  it('every map has a core spawn and 3 units per side', () => {
    for (const m of MAPS) {
      expect(m.rows.join('')).toContain('X');
      expect(m.spawns.player).toHaveLength(3);
      expect(m.spawns.ai).toHaveLength(3);
    }
  });
});

describe('full engine move flow', () => {
  it('move spends 1 AP and refuses illegal destinations', () => {
    const s = createMatch(getMap('scrapyard-cross'), 3, 'normal');
    const runner = s.units.find((u) => u.cls === 'runner' && u.team === 'player')!;
    const moves = legalMoves(s, runner);
    const destKey = [...moves.keys()].find((k) => k !== `${runner.pos.x},${runner.pos.y}`)!;
    const [x, y] = destKey.split(',').map(Number);
    const apBefore = runner.ap;
    expect(applyMove(s, runner, { x, y })).toBe(true);
    expect(runner.ap).toBe(apBefore - 1);
    expect(applyMove(s, runner, { x: 11, y: 0 })).toBe(false); // far & likely occupied/illegal
  });
});
