// Rustwake observability API — Node stdlib http only (no deps).
//   GET  /health  -> {"ok":true}
//   GET  /metrics -> uptime + match/log counters
//   POST /logs    -> {events:[...]} batches; shape-validated; 400 on junk;
//                    appends to logs/events.jsonl
// CORS is open to localhost so the Vite dev server can post from :5173.
//
// This file is plain ESM JavaScript with JSDoc types so it runs with zero
// build step: `npm run api`. (TypeScript types documented via @typedef.)

import http from 'node:http';
import { mkdirSync, appendFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const PORT = Number(process.env.RUSTWAKE_PORT || 8787);
const MAX_BODY_BYTES = 256 * 1024;

const __dirname = dirname(fileURLToPath(import.meta.url));
const LOG_DIR = join(__dirname, 'logs');
const LOG_FILE = join(LOG_DIR, 'events.jsonl');
mkdirSync(LOG_DIR, { recursive: true });

const KNOWN_EVENTS = new Set([
  'match_start',
  'turn_start',
  'move',
  'attack',
  'hit',
  'miss',
  'unit_down',
  'core_pickup',
  'core_drop',
  'match_end',
]);

const startedAt = Date.now();

/** In-memory counters surfaced by /metrics. */
const counters = {
  matches_started: 0,
  matches_completed: 0,
  wins_player: 0,
  wins_ai: 0,
  turns_played: 0,
  attacks: 0,
  hits: 0,
  log_events_received: 0,
};

/**
 * @typedef {Object} LogEvent
 * @property {string} type
 * @property {string} sessionId
 * @property {string} matchId
 * @property {number} turn
 * @property {number} ts
 * @property {Record<string, unknown>=} data
 */

/**
 * Validate one event; returns an error string or null.
 * @param {unknown} ev
 * @returns {string | null}
 */
function validateEvent(ev) {
  if (typeof ev !== 'object' || ev === null) return 'event not an object';
  const e = /** @type {Record<string, unknown>} */ (ev);
  if (typeof e.type !== 'string' || !KNOWN_EVENTS.has(e.type)) return `unknown type: ${String(e.type)}`;
  if (typeof e.sessionId !== 'string' || e.sessionId.length === 0) return 'bad sessionId';
  if (typeof e.matchId !== 'string' || e.matchId.length === 0) return 'bad matchId';
  if (typeof e.turn !== 'number' || !Number.isFinite(e.turn)) return 'bad turn';
  if (typeof e.ts !== 'number' || !Number.isFinite(e.ts)) return 'bad ts';
  if (e.data !== undefined && (typeof e.data !== 'object' || e.data === null)) return 'bad data';
  return null;
}

/**
 * Fold a validated event into the counters.
 * @param {any} ev
 */
function countEvent(ev) {
  counters.log_events_received++;
  switch (ev.type) {
    case 'match_start':
      counters.matches_started++;
      break;
    case 'match_end': {
      counters.matches_completed++;
      const turns = Number(ev.data?.turns ?? 0);
      if (Number.isFinite(turns)) counters.turns_played += turns;
      if (ev.data?.winner === 'player') counters.wins_player++;
      if (ev.data?.winner === 'ai') counters.wins_ai++;
      break;
    }
    case 'attack':
      counters.attacks++;
      break;
    case 'hit':
      counters.hits++;
      break;
  }
}

/**
 * @param {http.IncomingMessage} req
 * @returns {Promise<string>}
 */
function readBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on('data', (c) => {
      size += c.length;
      if (size > MAX_BODY_BYTES) {
        reject(new Error('body too large'));
        req.destroy();
        return;
      }
      chunks.push(c);
    });
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}

/**
 * @param {http.ServerResponse} res
 * @param {number} code
 * @param {unknown} body
 */
function sendJson(res, code, body) {
  const payload = JSON.stringify(body);
  res.writeHead(code, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  });
  res.end(payload);
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url ?? '/', `http://${req.headers.host ?? 'localhost'}`);

  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    });
    res.end();
    return;
  }

  if (req.method === 'GET' && url.pathname === '/health') {
    sendJson(res, 200, { ok: true });
    return;
  }

  if (req.method === 'GET' && url.pathname === '/metrics') {
    const uptime = Math.floor((Date.now() - startedAt) / 1000);
    const avg = counters.matches_completed > 0 ? counters.turns_played / counters.matches_completed : 0;
    sendJson(res, 200, {
      uptime,
      matches_started: counters.matches_started,
      matches_completed: counters.matches_completed,
      wins_player: counters.wins_player,
      wins_ai: counters.wins_ai,
      turns_played: counters.turns_played,
      attacks: counters.attacks,
      hits: counters.hits,
      avg_turns_per_match: Number(avg.toFixed(2)),
      log_events_received: counters.log_events_received,
    });
    return;
  }

  if (req.method === 'POST' && url.pathname === '/logs') {
    let raw;
    try {
      raw = await readBody(req);
    } catch {
      sendJson(res, 400, { ok: false, error: 'body too large' });
      return;
    }
    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch {
      sendJson(res, 400, { ok: false, error: 'invalid JSON' });
      return;
    }
    if (typeof parsed !== 'object' || parsed === null || !Array.isArray(parsed.events)) {
      sendJson(res, 400, { ok: false, error: 'expected {events:[...]}' });
      return;
    }
    if (parsed.events.length > 500) {
      sendJson(res, 400, { ok: false, error: 'batch too large' });
      return;
    }
    for (const ev of parsed.events) {
      const err = validateEvent(ev);
      if (err) {
        sendJson(res, 400, { ok: false, error: err });
        return;
      }
    }
    let lines = '';
    for (const ev of parsed.events) {
      countEvent(ev);
      lines += JSON.stringify(ev) + '\n';
    }
    try {
      appendFileSync(LOG_FILE, lines);
    } catch (err) {
      console.error('[api] failed to append events.jsonl', err);
    }
    sendJson(res, 200, { ok: true, accepted: parsed.events.length });
    return;
  }

  sendJson(res, 404, { ok: false, error: 'not found' });
});

server.listen(PORT, () => {
  console.log(`[rustwake-api] listening on http://localhost:${PORT}`);
  console.log(`[rustwake-api] appending events to ${LOG_FILE}`);
});

export { server, counters };
