/* ─── LocalStorage persistence with versioned keys ─── */

const VERSION = 1;
const KEY_PROFILES = 'staticline:v1:profiles';
const KEY_SETTINGS = 'staticline:v1:settings';
const KEY_MATCHES = 'staticline:v1:matches';
const KEY_DEMO_SEEDED = 'staticline:v1:demoSeeded';

/* ─── Defaults ─── */

const defaultSettings = {
  difficulty: 'standard',
  lengthClass: 'standard',
  ghostSpeed: 1,
  muted: false,
  timeCapSec: 60,
};

/* ─── Generic helpers ─── */

function readKey(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    if (raw === null) return fallback;
    const parsed = JSON.parse(raw);
    if (parsed === null || parsed === undefined) return fallback;
    // For arrays, validate it's actually an array
    if (Array.isArray(fallback) && !Array.isArray(parsed)) return fallback;
    return parsed;
  } catch {
    return fallback;
  }
}

function writeKey(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // localStorage full or unavailable — silently degrade
  }
}

/* ─── Public API ─── */

export function loadProfiles() {
  return readKey(KEY_PROFILES, []);
}

export function saveProfiles(profiles) {
  writeKey(KEY_PROFILES, profiles);
}

export function loadSettings() {
  const saved = readKey(KEY_SETTINGS, null);
  if (saved === null) return { ...defaultSettings };
  // Validate shape: merge with defaults to fill missing keys
  return { ...defaultSettings, ...saved };
}

export function saveSettings(settings) {
  writeKey(KEY_SETTINGS, settings);
}

export function loadMatches() {
  return readKey(KEY_MATCHES, []);
}

export function saveMatches(matches) {
  // Cap at 10 newest
  const capped = matches.slice(0, 10);
  writeKey(KEY_MATCHES, capped);
}

export function addMatch(match) {
  const matches = loadMatches();
  matches.unshift(match);
  saveMatches(matches);
}

export function loadDemoSeeded() {
  const val = readKey(KEY_DEMO_SEEDED, false);
  return val === true;
}

export function saveDemoSeeded(val) {
  writeKey(KEY_DEMO_SEEDED, val);
}

/** Reset all data to defaults */
export function resetAll() {
  try {
    localStorage.removeItem(KEY_PROFILES);
    localStorage.removeItem(KEY_SETTINGS);
    localStorage.removeItem(KEY_MATCHES);
    localStorage.removeItem(KEY_DEMO_SEEDED);
  } catch {
    // ignore
  }
}

/* ─── Version migration / safety ─── */
const KEY_SCHEMA_VERSION = 'staticline:schemaVersion';

export function checkSchemaVersion() {
  try {
    const v = parseInt(localStorage.getItem(KEY_SCHEMA_VERSION), 10);
    if (isNaN(v) || v < VERSION) {
      // Schema too old or missing — reset
      resetAll();
      localStorage.setItem(KEY_SCHEMA_VERSION, String(VERSION));
      return false;
    }
    return true;
  } catch {
    resetAll();
    return false;
  }
}

export function initSchema() {
  try {
    localStorage.setItem(KEY_SCHEMA_VERSION, String(VERSION));
  } catch {
    // ignore
  }
}
