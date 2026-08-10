import { all, run } from '../db.js';

// Simple wordlist-based filter. Admins manage the list via /api/moderation/banned-words.
let cache = null;
let cacheTime = 0;

function loadWords() {
  const now = Date.now();
  if (cache && now - cacheTime < 60_000) return cache;
  cache = all('SELECT word FROM banned_words').map((r) => r.word.toLowerCase());
  cacheTime = now;
  return cache;
}

export function invalidateWordCache() {
  cacheTime = 0;
}

export function scanText(text) {
  const lower = String(text).toLowerCase();
  const matches = loadWords().filter((w) => w && lower.includes(w));
  return { ok: matches.length === 0, matches };
}

export function seedDefaultWords() {
  const defaults = ['spamlink.example', 'buycheapfollowers'];
  for (const w of defaults) run('INSERT OR IGNORE INTO banned_words (word) VALUES (?)', w);
}
