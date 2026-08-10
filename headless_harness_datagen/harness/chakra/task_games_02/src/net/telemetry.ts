// Telemetry: structured JSON log events, buffered locally, batch-POSTed to the
// observability API. Never blocks the game; API offline just grows the buffer
// (capped FIFO 200). Telemetry opt-out is honored immediately.

import type { LogEvent, LogEventType } from '../core/types.js';
import { LOG_BUFFER_CAP, loadLogBuffer, loadSettings, saveLogBuffer } from '../core/persist.js';

const API_BASE = 'http://localhost:8787';

function sessionId(): string {
  try {
    let id = globalThis.localStorage?.getItem('rustwake.session');
    if (!id) {
      id = `s_${Date.now().toString(36)}_${Math.floor(Math.random() * 1e6).toString(36)}`;
      globalThis.localStorage?.setItem('rustwake.session', id);
    }
    return id;
  } catch {
    return 's_ephemeral';
  }
}

export class Telemetry {
  private buffer: LogEvent[] = [];
  private matchId = '';
  private turn = 0;
  private flushing = false;
  /** Live strip lines shown on-screen. */
  readonly strip: string[] = [];

  constructor() {
    this.buffer = loadLogBuffer();
  }

  setMatch(matchId: string): void {
    this.matchId = matchId;
  }

  setTurn(turn: number): void {
    this.turn = turn;
  }

  /** The LogSink handed to the rules engine. */
  sink = (e: { type: LogEventType; data?: Record<string, unknown> }): void => {
    if (loadSettings().telemetryOptOut) return; // honored immediately
    const ev: LogEvent = {
      type: e.type,
      sessionId: sessionId(),
      matchId: this.matchId,
      turn: this.turn,
      ts: Date.now(),
      data: e.data,
    };
    this.buffer.push(ev);
    if (this.buffer.length > LOG_BUFFER_CAP) this.buffer.shift();
    saveLogBuffer(this.buffer);
    this.pushStrip(ev);
    void this.flush();
  };

  private pushStrip(ev: LogEvent): void {
    const d = (ev.data ?? {}) as Record<string, unknown>;
    let line = ev.type;
    switch (ev.type) {
      case 'move': line = `${d.unit} moves`; break;
      case 'attack': line = `${d.attacker} shoots ${d.target} (${Math.round(Number(d.chance) * 100)}%)`; break;
      case 'hit': line = `HIT ${d.target} -${d.dmg}HP`; break;
      case 'miss': line = `MISS ${d.target}`; break;
      case 'unit_down': line = `${d.unit} is down!`; break;
      case 'core_pickup': line = `${d.unit} grabs the core!`; break;
      case 'core_drop': line = `Core dropped`; break;
      case 'turn_start': line = `— Turn ${d.turn} (${d.side}) —`; break;
      case 'match_end': line = `Match over: ${d.winner}`; break;
      case 'match_start': line = `Match start (seed ${d.seed})`; break;
    }
    this.strip.push(line);
    if (this.strip.length > 5) this.strip.shift();
  }

  /** Try to flush buffered events; silently keeps them when the API is down. */
  async flush(): Promise<void> {
    if (this.flushing || this.buffer.length === 0) return;
    this.flushing = true;
    const batch = [...this.buffer];
    try {
      const res = await fetch(`${API_BASE}/logs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ events: batch }),
      });
      if (res.ok) {
        this.buffer.splice(0, batch.length);
        saveLogBuffer(this.buffer);
      }
    } catch {
      /* API offline — buffer stays, game plays on */
    } finally {
      this.flushing = false;
    }
  }

  pendingCount(): number {
    return this.buffer.length;
  }
}

export async function fetchMetrics(): Promise<Record<string, unknown> | null> {
  try {
    const res = await fetch(`${API_BASE}/metrics`);
    if (!res.ok) return null;
    return (await res.json()) as Record<string, unknown>;
  } catch {
    return null;
  }
}
