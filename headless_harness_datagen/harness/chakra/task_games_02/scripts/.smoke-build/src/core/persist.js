// localStorage persistence with a `v` version field on every record.
const SAVE_KEY = 'rustwake.save';
const SETTINGS_KEY = 'rustwake.settings';
const HISTORY_KEY = 'rustwake.history';
const LOGBUFFER_KEY = 'rustwake.logbuffer';
const SAVE_VERSION = 1;
const SETTINGS_VERSION = 1;
const HISTORY_VERSION = 1;
const LOGBUFFER_VERSION = 1;
const LOG_CAP = 200;
const HISTORY_CAP = 10;
function safeGet(key) {
    try {
        return globalThis.localStorage?.getItem(key) ?? null;
    }
    catch {
        return null;
    }
}
function safeSet(key, value) {
    try {
        globalThis.localStorage?.setItem(key, value);
    }
    catch {
        /* storage unavailable — play sessionless */
    }
}
export function saveMatch(state) {
    safeSet(SAVE_KEY, JSON.stringify({ v: SAVE_VERSION, state }));
}
export function loadMatch() {
    const raw = safeGet(SAVE_KEY);
    if (!raw)
        return null;
    try {
        const parsed = JSON.parse(raw);
        if (parsed.v !== SAVE_VERSION || !parsed.state)
            return null;
        if (parsed.state.over)
            return null;
        return parsed.state;
    }
    catch {
        return null;
    }
}
export function clearMatch() {
    try {
        globalThis.localStorage?.removeItem(SAVE_KEY);
    }
    catch {
        /* noop */
    }
}
export function loadSettings() {
    const raw = safeGet(SETTINGS_KEY);
    if (raw) {
        try {
            const parsed = JSON.parse(raw);
            if (parsed.v === SETTINGS_VERSION) {
                return {
                    telemetryOptOut: !!parsed.telemetryOptOut,
                    seenControls: !!parsed.seenControls,
                };
            }
        }
        catch {
            /* fall through */
        }
    }
    return { telemetryOptOut: false, seenControls: false };
}
export function saveSettings(s) {
    safeSet(SETTINGS_KEY, JSON.stringify({ v: SETTINGS_VERSION, ...s }));
}
export function loadHistory() {
    const raw = safeGet(HISTORY_KEY);
    if (!raw)
        return [];
    try {
        const parsed = JSON.parse(raw);
        if (parsed.v !== HISTORY_VERSION || !Array.isArray(parsed.entries))
            return [];
        return parsed.entries;
    }
    catch {
        return [];
    }
}
export function pushHistory(entry) {
    const entries = [entry, ...loadHistory()].slice(0, HISTORY_CAP);
    safeSet(HISTORY_KEY, JSON.stringify({ v: HISTORY_VERSION, entries }));
}
export function loadLogBuffer() {
    const raw = safeGet(LOGBUFFER_KEY);
    if (!raw)
        return [];
    try {
        const parsed = JSON.parse(raw);
        if (parsed.v !== LOGBUFFER_VERSION || !Array.isArray(parsed.events))
            return [];
        return parsed.events;
    }
    catch {
        return [];
    }
}
export function saveLogBuffer(events) {
    const capped = events.slice(-LOG_CAP);
    safeSet(LOGBUFFER_KEY, JSON.stringify({ v: LOGBUFFER_VERSION, events: capped }));
}
export const LOG_BUFFER_CAP = LOG_CAP;
