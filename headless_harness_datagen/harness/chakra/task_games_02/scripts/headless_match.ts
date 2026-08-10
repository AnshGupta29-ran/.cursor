// Scripted headless match: drives both sides through the pure rules modules
// (player side uses the same utility scorer as Scrapbrain, always "normal")
// until a definite result or the turn cap. Emits structured log events that
// mirror what the browser client produces.

import { createMatch, beginSideTurn, endTurn } from '../src/core/game.js';
import { runAiTurn } from '../src/core/ai.js';
import { Rng } from '../src/core/rng.js';
import { getMap } from '../src/data/maps.js';
import type { LogEvent, LogEventType } from '../src/core/types.js';

export interface HeadlessResult {
  over: boolean;
  winner: string | null;
  turns: number;
  cause: string | null;
  seed: number;
  events: LogEvent[];
}

export function playHeadlessMatch(seed: number): HeadlessResult {
  const events: LogEvent[] = [];
  const sessionId = 's_smoke';
  const state = createMatch(getMap('scrapyard-cross'), seed, 'normal', 'm_smoke');

  const sink = (e: { type: LogEventType; data?: Record<string, unknown> }): void => {
    events.push({
      type: e.type,
      sessionId,
      matchId: state.matchId,
      turn: state.turn,
      ts: Date.now(),
      data: e.data,
    });
  };

  sink({ type: 'match_start', data: { mapId: state.mapId, difficulty: 'normal', seed } });
  const rng = new Rng(state.rng);
  beginSideTurn(state);

  let guard = 200;
  while (!state.over && guard-- > 0) {
    runAiTurn(state, state.active, rng, sink); // utility scorer drives BOTH sides headlessly
    if (state.over) break;
    endTurn(state, sink);
  }
  state.rng = rng.state();

  return {
    over: state.over,
    winner: state.winner,
    turns: state.turn,
    cause: state.endCause,
    seed,
    events,
  };
}
