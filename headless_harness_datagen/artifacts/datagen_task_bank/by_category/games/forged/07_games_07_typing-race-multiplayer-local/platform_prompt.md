# PLATFORM PROMPT — STATICLINE: Intercept Desk

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `javascript`
- **ui_surface:** `react_spa`
- **persistence:** `localstorage`
- **complexity:** `medium`
- Do **not** rewrite this project in a different language.

## Complexity & fidelity lock (datagen)
- Complexity band: **medium**
- UI fidelity: MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required
- Effort cue: deeper than low; still ship demoable without endless polish
- Anti-stub: FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.
- **Build-first (anti time-waste):** Implement immediately from this PRD. Forbidden: WebSearch/WebFetch, browsing docs sites, winget/ripgrep installs for searching, Explore/research subagents, Grep/Glob fishing across sibling tasks. At most 2 targeted reads inside this task workdir before Write/Edit. Low = few files shipped fast — do not gold-plate.

## 1. Project Request / Product identity
Build **STATICLINE**, a local-multiplayer typing race set in a 1970s numbers-station listening post. 2–4 players are rival intercept operators transcribing the same burst transmission. The twist: races are **asynchronous ghost relays** — players run one at a time on the shared keyboard while previously recorded opponents replay as live "ghost" progress lanes, so everyone still races head-to-head on one machine. A built-in **Demo Desk** mode plays a full match between two recorded operators (sample data) with zero input.

Stack is locked: **JavaScript, React SPA, localStorage persistence**. No backend, no netcode. Docker Compose optional convenience only.

## 2. Target users & primary jobs-to-be-done
- A staff engineer demoing a side project: wants `npm install && npm run dev` playable in <2 minutes, plus logic tests they can trust.
- Small groups (game night, classroom warm-up) who want a fair one-keyboard race with a clear winner screen and rematch.
- Solo users who want to watch the Demo Desk or race a recorded ghost.

## 3. Core requirements / entities
- **PlayerProfile** `{ id, name, color }` — 2–4 per match, unique names enforced.
- **Transmission** `{ id, text, difficulty, lengthClass }` — themed prompts loaded from a data file (`src/data/transmissions.js`), at least 12 entries across short/standard/burst classes. No lorem ipsum.
- **KeystrokeLog** `[{ t, char, correct }]` — timestamped per run; powers ghost replay.
- **RaceRun** `{ playerId, transmissionId, elapsedMs, wpm, accuracy, progress, keystrokeLog, status: finished|forfeit|timeout }`.
- **Match** `{ id, seed, transmissionId, runs[], winnerId, createdAt }`.
- **Settings** `{ difficulty, lengthClass, ghostSpeed, muted, timeCapSec }`.

## 4. Major feature areas
- **Main menu**: New Match, Demo Desk, History, Settings. Cohesive retro-terminal styling (phosphor palette, scanline CSS), not debug rectangles.
- **Roster setup**: add/edit 2–4 operators, auto-assign colors, reject duplicate/blank names.
- **Race loop**: countdown → per-player run. During a run show: the shared transmission with per-character correct/error highlighting, the active operator's progress bar ("signal lock"), live WPM ("key rate"), accuracy ("fidelity"), elapsed timer, and **ghost lanes replaying earlier runs in real time**.
- **Scoring**: WPM = (correct chars / 5) / minutes; accuracy = correct keystrokes / total keystrokes. Backspace allowed; corrections count as keystrokes. Paste disabled. Runs end on completion, forfeit (Esc), or time cap.
- **Winner screen**: ranked table (finished runs by elapsed time; unfinished by progress, then accuracy), winner call-sign, per-run stats, Rematch (same seed) and New Transmission (reseed) buttons.
- **Demo Desk**: one click plays a full 2-operator match using shipped sample KeystrokeLogs with realistic WPM curves and injected typos; user can adjust ghost speed or quit to menu.
- **History**: last 10 matches from localStorage with winners and stats; clear-history control.
- **Settings**: difficulty, length class, ghost replay speed (0.5×/1×/2×), mute, time cap (45/60/90s).

## 5. Domain-specific workflows
**Happy path:** Menu → New Match → add 3 operators → pick standard length → seeded transmission dealt → P1 runs solo → P2 runs while P1's ghost replays → P3 runs against both ghosts → winner screen → rematch.
**Edge cases:** duplicate names blocked; empty roster blocks start; a forfeit run still replays as a partial ghost; timeout marks run `timeout` and ranks below finishers; exact elapsed-time tie broken by accuracy then WPM (deterministic); corrupt localStorage payload falls back to defaults without crashing; replaying a ghost at 2× never desyncs from its KeystrokeLog.

## 6. Data & persistence
localStorage only, versioned keys: `staticline:v1:profiles`, `staticline:v1:settings`, `staticline:v1:matches` (capped at 10), `staticline:v1:demoSeeded`. All reads validated; schema version mismatch triggers safe reset. Transmissions and demo ghost data ship as source data files, not storage.

## 7. UX / API surface expectations
- Single-page app, hash or state-based views: Menu, Setup, Race, Results, History, Settings.
- Controls documented on-screen and in README: typing advances, Backspace corrects, Esc forfeits, Enter confirms.
- HUD readable at a glance: progress bars per lane with operator color + name, live WPM/accuracy, transmission pane with error highlighting.
- Seeded RNG (e.g., mulberry32) for transmission selection so matches and tests are reproducible.

## 8. Quality, security, and reliability expectations
- Pure logic modules separated from components: `src/lib/scoring.js`, `src/lib/race.js` (ranking/winner), `src/lib/rng.js`, `src/lib/ghost.js` (position at time t), `src/lib/storage.js`.
- No eval, no dangerouslySetInnerHTML, no external network calls; all assets local.
- Ghost replay must be a pure function of `(keystrokeLog, elapsedMs)` — same inputs, same rendered position, always.

## 9. Documentation & testing expectations
- **Vitest** unit tests (light, no GUI tests) covering: WPM/accuracy math, winner ranking incl. tie-breaks and forfeits, seeded transmission pick determinism, ghost position at t (including beyond-log and 2× speed), storage validation/fallback.
- README: fantasy summary, controls, how the relay/ghost fairness works, run/test/build commands, design notes on scoring and replay determinism, known limitations.

## 10. Constraints & non-goals
- No accounts, no server, no real-time multiplayer netcode, no external prompt APIs.
- No heavy deps: React + Vite + Vitest only; no state-management library unless clearly justified.
- Docker Compose optional (`docker-compose.yml` for a static-serve of the build); `npm run dev` must work with zero Docker.
- No placeholder prompts, no generic typing-test clone copy.

## 11. Acceptance criteria
- [ ] App launches to a styled menu; a full 2–4 player relay match is playable end-to-end.
- [ ] Ghost lanes replay prior runs deterministically during subsequent runs.
- [ ] WPM, accuracy, and progress bars update live and match README formulas.
- [ ] Winner screen ranks correctly, handles forfeit/timeout/ties, offers rematch/reseed.
- [ ] Demo Desk plays a complete sample-data match with no keyboard input.
- [ ] Settings, profiles, and last-10 history persist across reload via versioned localStorage keys with safe fallback.
- [ ] `npm test` passes ≥ 12 unit assertions across the four logic modules.
- [ ] README enables a first play session without outside help.

## 12. Uniqueness / anti-clone constraints
- The async **ghost-relay on one keyboard** is the defining mechanic; do not substitute simultaneous-focus pseudo-multiplayer.
- Transmissions must be in-fiction (intercepted bursts, coordinates, code phrases), not lorem ipsum or quote-db dumps.
- Terminology stays diegetic in UI copy: operators, transmissions, signal lock, key rate, fidelity.
- No "Todo app" energy: any static, non-interactive, or placeholder-only screen is a failure condition.
