// Main-thread client for the Scrapbrain worker. 2s timeout per decision; on
// worker failure/timeout, falls back to main-thread scoring and logs a warning.

import type { GameState, RngState, Unit } from '../core/types.js';
import { decideForUnit, type AiAction } from '../core/ai.js';

const TIMEOUT_MS = 2000;

let worker: Worker | null = null;
let workerFailed = false;

function getWorker(): Worker | null {
  if (workerFailed) return null;
  if (!worker) {
    try {
      worker = new Worker(new URL('./scrapbrain.worker.ts', import.meta.url), { type: 'module' });
    } catch (err) {
      console.warn('[scrapbrain] worker unavailable, using main-thread fallback', err);
      workerFailed = true;
      return null;
    }
  }
  return worker;
}

export interface AiDecision {
  action: AiAction;
  rng: RngState;
  usedFallback: boolean;
}

export function decideWithWorker(
  state: GameState,
  unit: Unit,
  rng: RngState,
): Promise<AiDecision> {
  const w = getWorker();
  if (!w) {
    const r = decideForUnit(state, unit.id, rng);
    return Promise.resolve({ action: r.action, rng: r.rngState, usedFallback: true });
  }
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      console.warn('[scrapbrain] worker timeout — main-thread fallback');
      workerFailed = true;
      try {
        w.terminate();
      } catch {
        /* noop */
      }
      worker = null;
      const r = decideForUnit(state, unit.id, rng);
      resolve({ action: r.action, rng: r.rngState, usedFallback: true });
    }, TIMEOUT_MS);

    const onMsg = (ev: MessageEvent) => {
      clearTimeout(timer);
      w.removeEventListener('message', onMsg);
      w.removeEventListener('error', onErr);
      const data = ev.data as { ok: boolean; action?: AiAction; rng?: RngState; error?: string };
      if (data.ok && data.action && data.rng) {
        resolve({ action: data.action, rng: data.rng, usedFallback: false });
      } else {
        console.warn('[scrapbrain] worker error — main-thread fallback', data.error);
        const r = decideForUnit(state, unit.id, rng);
        resolve({ action: r.action, rng: r.rngState, usedFallback: true });
      }
    };
    const onErr = (ev: ErrorEvent) => {
      clearTimeout(timer);
      w.removeEventListener('message', onMsg);
      w.removeEventListener('error', onErr);
      console.warn('[scrapbrain] worker crashed — main-thread fallback', ev.message);
      workerFailed = true;
      const r = decideForUnit(state, unit.id, rng);
      resolve({ action: r.action, rng: r.rngState, usedFallback: true });
    };
    w.addEventListener('message', onMsg);
    w.addEventListener('error', onErr);
    try {
      w.postMessage({ state, unitId: unit.id, rng });
    } catch (err) {
      clearTimeout(timer);
      console.warn('[scrapbrain] postMessage failed — main-thread fallback', err);
      const r = decideForUnit(state, unit.id, rng);
      resolve({ action: r.action, rng: r.rngState, usedFallback: true });
    }
  });
}
