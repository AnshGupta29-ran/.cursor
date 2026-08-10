// Hit-chance math and attack resolution. Pure, dependency-free.

import { Rng } from './rng.js';
import {
  GameState,
  Unit,
  UNIT_STATS,
  manhattan,
} from './types.js';
import { los } from './los.js';

export const BASE_HIT = 0.8;
export const COVER_HIT = 0.55;

export interface ShotPreview {
  canShoot: boolean;
  reason: string | null;
  /** Hit probability in [0,1] (0 when the shot is impossible). */
  chance: number;
  halfCover: boolean;
  dmg: number;
}

/** Preview the shot attacker -> target without mutating state. */
export function previewShot(state: GameState, attacker: Unit, target: Unit): ShotPreview {
  const stats = UNIT_STATS[attacker.cls];
  const dist = manhattan(attacker.pos, target.pos);
  if (!target.alive) {
    return { canShoot: false, reason: 'Target down', chance: 0, halfCover: false, dmg: stats.dmg };
  }
  if (dist > stats.range) {
    return { canShoot: false, reason: 'Out of range', chance: 0, halfCover: false, dmg: stats.dmg };
  }
  const r = los(state.board, attacker.pos, target.pos);
  if (!r.clear) {
    return { canShoot: false, reason: 'Blocked by container', chance: 0, halfCover: false, dmg: stats.dmg };
  }
  const coverApplies = r.halfCover && !stats.ignoresHalfCover;
  const chance = coverApplies ? COVER_HIT : BASE_HIT;
  return { canShoot: true, reason: null, chance, halfCover: coverApplies, dmg: stats.dmg };
}

export interface ShotOutcome {
  hit: boolean;
  chance: number;
  dmg: number;
  targetDown: boolean;
}

/** Resolve an attack; mutates target hp/alive. Uses the match RNG for determinism. */
export function resolveAttack(state: GameState, rng: Rng, attacker: Unit, target: Unit): ShotOutcome {
  const preview = previewShot(state, attacker, target);
  if (!preview.canShoot) {
    return { hit: false, chance: 0, dmg: 0, targetDown: false };
  }
  const roll = rng.next();
  const hit = roll < preview.chance;
  let targetDown = false;
  if (hit) {
    target.hp = Math.max(0, target.hp - preview.dmg);
    if (target.hp === 0) {
      target.alive = false;
      targetDown = true;
    }
  }
  return { hit, chance: preview.chance, dmg: hit ? preview.dmg : 0, targetDown };
}
