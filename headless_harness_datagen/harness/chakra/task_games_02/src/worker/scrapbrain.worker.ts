// Scrapbrain Web Worker: runs AI utility scoring off the main thread.
// Protocol:
//   in:  { state: GameState, unitId: string, rng: RngState }
//   out: { ok: true, action, rng } | { ok: false, error }

import { decideForUnit } from '../core/ai.js';
import type { GameState, RngState } from '../core/types.js';

export interface WorkerRequest {
  state: GameState;
  unitId: string;
  rng: RngState;
}

export interface WorkerResponse {
  ok: boolean;
  action?: unknown;
  rng?: RngState;
  error?: string;
}

self.onmessage = (ev: MessageEvent<WorkerRequest>) => {
  try {
    const { state, unitId, rng } = ev.data;
    const result = decideForUnit(state, unitId, rng);
    const resp: WorkerResponse = { ok: true, action: result.action, rng: result.rngState };
    (self as unknown as Worker).postMessage(resp);
  } catch (err) {
    const resp: WorkerResponse = { ok: false, error: String(err) };
    (self as unknown as Worker).postMessage(resp);
  }
};
