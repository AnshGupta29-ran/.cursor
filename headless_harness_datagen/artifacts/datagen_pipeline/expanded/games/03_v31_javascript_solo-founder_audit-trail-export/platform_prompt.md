# VARIANT v31_javascript_solo-founder_audit-trail-export - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `javascript`
- **user_persona**: `solo_founder`
- **novelty_hook**: `audit_trail_export`
- **ui_surface**: `html_canvas`
- **persistence**: `sqlite`
- **complexity**: `low`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `javascript`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v31_javascript_solo-founder_audit-trail-export`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v31_javascript_solo-founder_audit-trail-export` when demoable.

---

## BASE PRD (honor unless mutated above)

# RegRun — Compliance Courier Ops

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `javascript`
- **ui_surface:** `react_spa`
- **persistence:** `sqlite`
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

## 1. Project Request / Product Identity

Build **RegRun**, an endless-runner micro-game an enterprise L&D or compliance lead can drop onto an intranet to make security-awareness training measurable and repeatable. The player is a **Compliance Courier** sprinting across a procedurally generated **risk landscape**, vaulting **Audit Findings**, ducking under **Policy Gaps**, and grabbing **Control Badges** for score multipliers. Distance survived = "coverage meters"; difficulty escalates through named **Risk Tiers**. One twist: a **Daily Audit Seed** — everyone in the org runs the identical course each day, feeding a department leaderboard. One extension point: a **plugin hook** for custom obstacle/training packs, shipped with one working stub plugin.

Stack is locked: **JavaScript everywhere, React SPA client (canvas-rendered game), Node/Express server, SQLite persistence**, delivered as a **monorepo (`/client`, `/server`, `/plugins`)**.

## 2. Target Users & Jobs-to-be-Done

- **Compliance program owner (buyer):** deploy on-prem with zero external calls, view participation via run history, extend content without a vendor engagement.
- **Employee (player):** play a 60–120 second session, compete on today's seed, restart instantly after a wipeout.
- **Developer/integrator:** add a training-pack plugin against a documented contract.

## 3. Core Requirements / Entities

- **Run**: id, callsign, seed, mode (`daily`|`practice`), distance_m, risk_tier_reached, badges, duration_ms, created_at.
- **Player**: callsign only (typed at menu; no auth, no passwords).
- **Obstacle classes**: `AuditFinding` (ground block → jump), `PolicyGap` (overhead bar → slide), `DeadlineGate` (paired block+bar). AABB collision, documented.
- **Pickup**: `ControlBadge` — +1 combo multiplier (max ×5); a hit resets combo, not the run.
- **RiskTier**: `tier = floor(distance / 250)`; scroll speed, spawn density, and pattern table scale per tier via a documented formula.
- **Plugin descriptor**: name, version, obstacle types contributed, spawn rules.

## 4. Major Feature Areas

- **Core loop (canvas in a React component):** auto-run, Space/↑ jump, ↓ slide, P/Esc pause. Deterministic seeded RNG (mulberry32); same seed + same inputs → same course. Target 60fps with simple vector shapes (cohesive palette, not debug rectangles).
- **Procedural generation:** pattern-based spawner (gap table per tier), guarantees survivable spacing; pure functions in `client/src/game/` separable from rendering.
- **Difficulty ramp:** tier-ups announced in HUD; speed/density formulas documented in README.
- **Daily Audit Seed:** server derives today's seed (UTC date hash); client fetches it for `daily` mode; `practice` uses a random seed.
- **Restart flow:** game-over panel with run summary (meters, tier, badges, personal best), **R** to restart same mode, **M** for menu.
- **Persistence & leaderboard:** server saves each finished run; top-10 leaderboard filterable by seed; settings (mute, difficulty assist, reduced motion) saved per callsign.
- **Plugin hook:** server scans `/plugins/*/plugin.json` + `index.js` exporting `register(api)` where `api` exposes `addObstacleType(def)` and `addSpawnRule(fn)`. Ship stub plugin **phishing-surge** adding a `PhishNet` overhead obstacle at tier ≥ 2. Expose loaded plugins at `GET /api/plugins`; document authoring in README.

## 5. Workflows

**Happy path:** open app → enter callsign → menu → "Daily Audit" → run → collide → game-over summary auto-posted → press R → new run → leaderboard shows placement.

**Edge cases:** server unreachable → client plays offline, stores run in localStorage flagged `unsynced`, leaderboard panel shows "offline"; duplicate callsign allowed (leaderboard keys on run id); tab blur auto-pauses; invalid plugin manifest is skipped with a server log line, never a crash; SQLite file created/migrated on first boot.

## 6. Data & Persistence

SQLite (better-sqlite3 or sqlite3) at `server/data/regrun.db`. Tables: `runs`, `settings(callsign PK, json)`. No ORM required; migrations = idempotent `CREATE TABLE IF NOT EXISTS`. All data local — no telemetry, no external network calls (procurement requirement).

## 7. UX / API Surface

React SPA: Menu, Game (canvas + HUD: meters, tier, combo, speed), Game Over, Leaderboard, Settings. Controls overlay on first run; colorblind-safe palette; assist mode (slower base speed) toggle.

API: `GET /api/health` · `GET /api/seed/today` · `POST /api/runs` · `GET /api/leaderboard?seed=&limit=` · `GET /api/plugins` · `GET/PUT /api/settings/:callsign`. JSON, validated bodies, 4xx on bad input.

## 8. Quality, Security, Reliability

Deterministic rules documented; seeded RNG unit-testable; server validates run payloads (plausibility bounds, reject NaN/negative); no eval of plugin code beyond `require` of local files; parameterized SQL only; graceful shutdown closes DB.

## 9. Documentation & Testing

README: run commands (`npm install`, `npm run dev` for client+server, `npm start` for prod), controls, win/lose rules, difficulty formulas, plugin authoring guide, known limitations. `npm run smoke`: boots server + built client, drives a headless browser (Playwright or equivalent) asserting menu renders, canvas paints non-blank pixels, and a posted run appears in the leaderboard; if no headless browser is available, fall back to HTTP-level assertions and document the fallback. Plus one small unit-test file covering RNG determinism and the tier/spawn math.

## 10. Constraints & Non-Goals

No auth, no multiplayer, no assets beyond code-drawn shapes, no build step heavier than Vite, no external CDNs/fonts, no multi-GB deps. Not a full training platform — no user management or reporting dashboards.

## 11. Acceptance Criteria

- [ ] `npm run dev` serves playable game; jump/slide/pause/restart (R) all work
- [ ] Seeded generation is deterministic; daily mode uses server seed
- [ ] Difficulty visibly ramps across tiers; game-over posts run to SQLite
- [ ] Leaderboard and settings persist across server restarts
- [ ] Stub plugin loads, appears in `/api/plugins`, and its obstacle spawns at tier ≥ 2
- [ ] Offline mode degrades gracefully; `npm run smoke` passes
- [ ] README enables first play in under 2 minutes

## 12. Uniqueness / Anti-Clone Rules

Not a generic Dino clone: compliance-courier fantasy, named obstacle classes, Risk Tier system, Daily Audit Seed leaderboard, and the plugin contract are mandatory vocabulary and mechanics. No placeholder UI, no "TODO" screens, no tutorial-app copy. All copy uses domain-authentic training terminology.
