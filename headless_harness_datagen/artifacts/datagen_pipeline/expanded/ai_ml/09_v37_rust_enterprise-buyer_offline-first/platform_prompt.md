# VARIANT v37_rust_enterprise-buyer_offline-first - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `rust`
- **user_persona**: `enterprise_buyer`
- **novelty_hook**: `offline_first`
- **ui_surface**: `desktop_window`
- **persistence**: `json_file`
- **complexity**: `medium`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `rust`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v37_rust_enterprise-buyer_offline-first`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v37_rust_enterprise-buyer_offline-first` when demoable.

---

## BASE PRD (honor unless mutated above)

# Sluicegate — Lexical Moderation Gate with Live Ops Window

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `rust`
- **ui_surface:** `game_loop_window`
- **persistence:** `sqlite`
- **complexity:** `hard`
- Do **not** rewrite this project in a different language.

## Complexity & fidelity lock (datagen)
- Complexity band: **hard**
- UI fidelity: HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable
- Effort cue: deepest; more entities, edges, and verification — still no wall-clock stop
- Anti-stub: FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.
- **Build-first (anti time-waste):** Implement immediately from this PRD. Forbidden: WebSearch/WebFetch, browsing docs sites, winget/ripgrep installs for searching, Explore/research subagents, Grep/Glob fishing across sibling tasks. At most 2 targeted reads inside this task workdir before Write/Edit. Low = few files shipped fast — do not gold-plate.


## 1. Project Request / Product Identity

Build **Sluicegate**, a deterministic toxicity/profanity screening service for real-time chat platforms (game lobbies, livestream chat, community forums). It exposes batch and streaming HTTP endpoints, persists every verdict to SQLite, and ships with a **native game-loop window** — a 60fps "moderation ops console" that renders verdicts as a live severity-colored ticker with rate sparklines.

**Stack (locked):** Rust (stable), `axum` + `tokio` for HTTP/SSE, `rusqlite` (bundled SQLite) for persistence, `macroquad` for the game-loop window. No ML model downloads — detection is a documented, deterministic normalization + lexicon pipeline (see §4). One command must boot everything: `cargo run --release` (or `./dev.sh`) starts API on `:8080` and opens the window; `--headless` runs API-only for CI.

**Persona voice:** this PRD is written by a staff engineer — expect explicit tradeoffs, failure semantics, and checkable acceptance.

## 2. Target Users & Jobs-to-be-Done

- **Trust-and-safety integrator**: embed a screening call before persisting chat messages; needs sub-10ms local verdicts and structured evidence.
- **Community moderator**: watch the live window during an event; needs severity-tiered visibility, not a boolean.
- **Ops engineer**: needs auditability (every verdict persisted) and a chaos drill path to prove the write pipeline survives DB faults.

## 3. Core Entities

- `LexiconTerm { term, category, severity_tier (T1 profanity / T2 harassment / T3 slur-threat), locale }` — seeded from a vendored JSON file, versioned.
- `AllowlistEntry { scope (tenant/channel), pattern, is_prefix }` — overrides lexicon matches (e.g., a medical channel allows anatomical terms).
- `ScreenVerdict { id, tenant, input_hash, action, score, tier_max, evidence_json, latency_us, created_at }` — append-only audit record.
- `ChaosState { enabled, drop_rate }` — runtime-toggleable, single row.

## 4. Major Feature Areas

**Normalization + matching pipeline (the "model"):**
1. Unicode case-fold, strip zero-width/diacritic characters, collapse repeated chars (`loooool` → `lool`→`lol`), map a small vendored leetspeak/homoglyph table (`4→a`, `0→o`, `@→a`).
2. Tokenize; match lexicon terms as whole tokens first, then substring matches on normalized tokens.
3. Score: `tier_weight × match_confidence` where confidence = 1.0 exact token, 0.8 normalized, 0.6 substring. Map score to `ALLOW / REVIEW / BLOCK` via configurable thresholds (env or config file).
4. Output schema: `{ action, score, tier_max, evidence: [{ span: [start,end], matched, term_category, confidence, overridden_by_allowlist }] }` — top-k evidence spans, byte offsets into the *original* input.

**Endpoints:**
- `POST /v1/screen` — single text → verdict JSON.
- `POST /v1/screen:batch` — JSON array → array of verdicts, per-item error isolation.
- `POST /v1/screen:stream` — NDJSON lines in, NDJSON verdicts out, flushed per line (chat-replay simulation).
- `GET /v1/events` — SSE broadcast of every verdict (feeds the window).
- `GET/POST/DELETE /v1/allowlist` — scoped allowlist management.
- `GET /v1/health` — includes `pending_writes` and `chaos` state.
- `POST /v1/chaos {enabled, drop_rate}` — runtime chaos toggle.

**Chaos toggle (recoverable failure path — required novelty):** when enabled (flag `--chaos`, endpoint, or pressing `C` in the window), SQLite writes randomly fail at `drop_rate` (default 0.25) via an injected error in the persistence layer. Verdicts must **still be returned to callers**; failed writes go to an in-memory retry buffer drained with backoff. `pending_writes` exposes buffer depth; the window shows a red "CHAOS — buffering N writes" banner. Disabling chaos drains the buffer to zero with **no verdict loss and no crash**.

**Game-loop window (macroquad, 60fps):** scrolling verdict ticker (severity-colored chips: green/yellow/red), verdicts/sec sparkline, ALLOW/REVIEW/BLOCK counters, chaos banner, keybindings `C` toggle chaos, `Space` pause feed. Connects via SSE; `--headless` skips it entirely.

## 5. Domain Workflows

**Happy path:** client POSTs a chat message → normalize → lexicon match → allowlist check (matching entries mark evidence `overridden`, suppressing the action) → score → persist verdict → return JSON → SSE emits → window ticks.

**Edge cases that must behave:** empty string (400 with code `EMPTY_INPUT`); input > 8KB (413); invalid UTF-8 (422); unknown tenant scope on allowlist write (400); batch with one corrupt item (that item errors, others succeed); lexicon file missing at boot (refuse to start with a clear message); 50 rapid chaos toggles (no deadlock, buffer drains).

## 6. Data & Persistence

SQLite at `./sluicegate.db` (path via env). Schema created by embedded migrations on boot — idempotent. Verdicts are append-only, indexed on `created_at` and `action`. Lexicon + allowlist seed data versioned (`schema_version` table). No external DB, no network fetches at runtime.

## 7. UX / API Surface

- README documents every endpoint with runnable `curl` examples that must actually succeed against a fresh boot.
- Errors are structured: `{ error: { code, message } }` with correct status codes; validation failures (4xx) are distinguishable from internal failures (5xx).
- First-run: `dev.sh` optionally seeds a sample tenant and prints three ready-to-paste curls (clean, T1, T3).

## 8. Quality, Security, Reliability

- Input size caps; no panics on malformed input — every handler returns structured errors.
- `action` thresholds configurable without recompile (TOML config + env overrides).
- Concurrent requests safe: SQLite behind a connection pool or serialized writer; chaos buffer bounded (shed with explicit 503 + `Retry-After` past 10k pending).

## 9. Documentation & Testing

**Tests (must pass with `cargo test`):**
- Unit tests on a **fixture corpus** (`fixtures/cases.json`): ≥25 labeled cases covering exact/normalized/substring matches, leetspeak evasion (`f4gg0t`-style obfuscation of fixture terms — keep fixtures synthetic, e.g., invented slur-like tokens like `gronk`/`zibble` mapped to T3 to avoid shipping real slurs in the repo), allowlist override, empty input, unicode zero-width injection.
- Unit test: chaos injection at drop_rate 1.0 → all writes buffered → disable → drained, all rows present.
- Smoke test (`scripts/smoke.sh`): boots headless on a random port, curls screen/batch/stream/health/chaos round-trip, asserts JSON shape, exits non-zero on failure. Must complete in <30s and **not** require a display.

**README:** architecture sketch, normalization stages, how to extend the lexicon, limitations section (deterministic pipeline = no semantic/context understanding; English-biased lexicon; evasion arms race; fixture tokens are synthetic).

## 10. Constraints & Non-Goals

- No ML model downloads, no GPU, no network calls at runtime.
- Not a full moderation dashboard (no auth, single-process, no user accounts).
- No real slur lists committed — synthetic fixture terms only, with a documented path to import a real lexicon.
- Window must not be required for the service to function.

## 11. Acceptance Criteria

- [ ] `./dev.sh` or `cargo run` boots API + window with one command; `--headless` boots API only.
- [ ] `POST /v1/screen` returns the full schema (action, score, tier_max, evidence spans with byte offsets).
- [ ] Batch endpoint isolates per-item errors; stream endpoint flushes NDJSON per line.
- [ ] Allowlist POST → subsequent matching input returns `ALLOW` with `overridden: true` evidence.
- [ ] Chaos on at 1.0 drop rate: `/v1/health` shows `pending_writes > 0`; chaos off: drains to 0; row count in SQLite equals total screened.
- [ ] Every verdict (including chaos-buffered ones) is queryable in SQLite.
- [ ] `cargo test` passes (fixtures + chaos recovery); `scripts/smoke.sh` passes headlessly.
- [ ] README curl examples succeed verbatim against a fresh boot.
- [ ] Window renders live verdicts with severity colors and chaos banner; `C` toggles chaos end-to-end.

## 12. Uniqueness / Anti-Clone Constraints

- Not a boolean "is_bad" toy: severity tiers, evidence spans, confidence, and allowlist override semantics are mandatory.
- No placeholder UI: the window must render real streamed verdicts, not static text.
- Use domain-authentic vocabulary throughout (verdict, tier, evidence span, tenant scope) — no "todo", no "item", no lorem ipsum.
- Synthetic lexicon tokens only (`gronk`, `zibble`, etc.) — this is both a safety constraint and a fingerprint for this run.

- Give website link when completed and run it automatically in my browser when full task is successfully implemented with full features , frontend , backend and everything working in the platform.
