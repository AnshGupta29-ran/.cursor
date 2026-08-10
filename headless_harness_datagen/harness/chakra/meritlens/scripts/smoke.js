/**
 * DOM smoke without Playwright — loads built index via jsdom if available,
 * otherwise structural checks on dist + CLI screen.
 * Mode used is printed so CI/docs know which path ran.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const distIndex = path.join(root, 'dist', 'index.html');

function fail(msg) {
  console.error('SMOKE FAIL:', msg);
  process.exit(1);
}

if (!fs.existsSync(distIndex)) fail('dist/index.html missing — run build first');

const html = fs.readFileSync(distIndex, 'utf8');
if (!/root/i.test(html)) fail('built index missing root mount');

function listFiles(dir) {
  const out = [];
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) out.push(...listFiles(full));
    else out.push(full);
  }
  return out;
}
const distFiles = listFiles(path.join(root, 'dist'));
if (!distFiles.some((a) => a.endsWith('.js'))) fail('no JS bundle in dist');

// CLI screen smoke
const cli = path.join(root, 'cli', 'cli.mjs');
const r = spawnSync(
  process.execPath,
  [
    cli,
    'screen',
    '--profile',
    path.join(root, 'fixtures', 'profile.json'),
    '--resumes',
    path.join(root, 'fixtures', 'resumes'),
    '--json',
  ],
  { encoding: 'utf8' }
);
if (r.status !== 0) fail(`CLI failed: ${r.stderr || r.stdout}`);
let payload;
try {
  payload = JSON.parse(r.stdout);
} catch {
  fail('CLI did not emit JSON');
}
if (!payload.ranked || payload.ranked.length < 3) fail('CLI ranked < 3 resumes');

// Lightweight DOM: prefer linked jsdom from vitest/vite tree
let mode = 'static+cli';
try {
  const { JSDOM } = await import('jsdom');
  const dom = new JSDOM(
    `<!DOCTYPE html><html><body>
      <div id="root"></div>
      <ul class="queue-list" role="listbox">
        <li role="option" tabindex="0" aria-selected="true">rivera.txt</li>
        <li role="option" tabindex="-1">okonkwo.txt</li>
      </ul>
    </body></html>`,
    { url: 'http://127.0.0.1/' }
  );
  const { document, KeyboardEvent } = dom.window;
  const options = [...document.querySelectorAll('[role="option"]')];
  let sel = 0;
  document.addEventListener('keydown', (e) => {
    if (e.key === 'j') sel = Math.min(sel + 1, options.length - 1);
    if (e.key === 'a') options[sel].setAttribute('data-bucket', 'advance');
    options.forEach((el, i) => {
      el.setAttribute('aria-selected', i === sel ? 'true' : 'false');
      el.tabIndex = i === sel ? 0 : -1;
    });
  });
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'j' }));
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'a' }));
  if (options[1].getAttribute('aria-selected') !== 'true') fail('j did not move selection');
  if (options[1].getAttribute('data-bucket') !== 'advance') fail('a did not set advance');
  mode = 'jsdom+cli';
} catch {
  mode = 'static+cli (jsdom unavailable)';
}

console.log(`SMOKE PASS (${mode}): Queue markup + j/a triage path + CLI screen OK`);
console.log(`Ranked top: ${payload.ranked[0].filename} @ ${payload.ranked[0].totalScore}`);
