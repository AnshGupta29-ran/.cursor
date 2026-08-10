// Smoke test: boots the observability API on a scratch port, asserts /health
// and /metrics shape, plays a scripted headless match through the compiled
// logic modules to a definite result within 40 turns, and POSTs the logs.
// Non-zero exit on any failure.

import { spawn } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';
import { execSync } from 'node:child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const PORT = 8891;
const BASE = `http://localhost:${PORT}`;

let failures = 0;
function assert(cond, msg) {
  if (cond) {
    console.log(`  ok  ${msg}`);
  } else {
    console.error(`  FAIL ${msg}`);
    failures++;
  }
}

// Compile the rules modules + headless runner with the project's TypeScript.
console.log('[smoke] compiling headless runner…');
try {
  execSync(
    'npx tsc -p tsconfig.smoke.json',
    { cwd: ROOT, stdio: 'inherit' },
  );
} catch (err) {
  // tsc emits JS even with type errors; continue if the output exists.
  console.warn('[smoke] tsc reported diagnostics (continuing if output exists)');
}

const runnerPath = join(ROOT, 'scripts', '.smoke-build', 'scripts', 'headless_match.js');
const { playHeadlessMatch } = await import(pathToFileURL(runnerPath).href);

// --- boot API ---------------------------------------------------------------
console.log('[smoke] booting API on :%d…', PORT);
const api = spawn(process.execPath, [join(ROOT, 'server', 'api.mjs')], {
  env: { ...process.env, RUSTWAKE_PORT: String(PORT) },
  stdio: ['ignore', 'pipe', 'pipe'],
});
api.stdout.on('data', (d) => process.stdout.write(`[api] ${d}`));
api.stderr.on('data', (d) => process.stderr.write(`[api] ${d}`));
api.on('exit', (code) => {
  if (code !== null && code !== 0) console.error(`[api] exited early with code ${code}`);
});

async function waitForHealth(timeoutMs = 8000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(`${BASE}/health`);
      if (res.ok) return true;
    } catch {
      /* not up yet */
    }
    await new Promise((r) => setTimeout(r, 150));
  }
  return false;
}

try {
  assert(await waitForHealth(), 'GET /health responds 200 within timeout');

  const health = await (await fetch(`${BASE}/health`)).json();
  assert(health.ok === true, '/health body is {"ok":true}');

  const m0 = await (await fetch(`${BASE}/metrics`)).json();
  const required = [
    'uptime',
    'matches_started',
    'matches_completed',
    'wins_player',
    'wins_ai',
    'turns_played',
    'attacks',
    'hits',
    'avg_turns_per_match',
    'log_events_received',
  ];
  assert(
    required.every((k) => typeof m0[k] === 'number'),
    '/metrics exposes all required numeric counters',
  );

  // Junk rejection.
  const bad = await fetch(`${BASE}/logs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ events: [{ type: 'nonsense' }] }),
  });
  assert(bad.status === 400, 'POST /logs rejects junk with 400');

  // --- headless match ---------------------------------------------------------
  console.log('[smoke] playing scripted headless match…');
  const result = playHeadlessMatch(20260731);
  assert(result.over === true, 'match reaches a definite result');
  assert(result.turns <= 40, `match ends within 40 turns (took ${result.turns})`);
  assert(['player', 'ai', 'draw'].includes(result.winner), `winner is definite (${result.winner})`);
  assert(result.events.length > 0, `match emitted ${result.events.length} log events`);
  const types = new Set(result.events.map((e) => e.type));
  for (const t of ['match_start', 'turn_start', 'attack', 'match_end']) {
    assert(types.has(t), `event type emitted: ${t}`);
  }

  // --- POST the match logs ----------------------------------------------------
  const post = await fetch(`${BASE}/logs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ events: result.events }),
  });
  assert(post.status === 200, 'POST /logs accepts a valid batch');
  const posted = await post.json();
  assert(posted.accepted === result.events.length, `API accepted ${posted.accepted} events`);

  const m1 = await (await fetch(`${BASE}/metrics`)).json();
  assert(m1.matches_started === m0.matches_started + 1, 'matches_started increments after a match');
  assert(m1.matches_completed === m0.matches_completed + 1, 'matches_completed increments after a match');
  assert(m1.log_events_received >= m0.log_events_received + result.events.length, 'log_events_received grows');
  assert(m1.attacks > m0.attacks, 'attacks counter grows');
} finally {
  // Shut the API child down cleanly: end stdio first, then kill, then wait
  // for exit before terminating the parent (avoids a libuv handle assertion
  // on Windows when exiting with live child pipes).
  try {
    api.stdout.destroy();
    api.stderr.destroy();
    api.kill();
    await new Promise((resolve) => {
      const t = setTimeout(resolve, 1500);
      api.once('exit', () => {
        clearTimeout(t);
        resolve();
      });
    });
  } catch {
    /* best effort */
  }
}

if (failures > 0) {
  console.error(`[smoke] ${failures} failure(s)`);
  process.exit(1);
}
console.log('[smoke] all checks passed');
process.exit(0);
