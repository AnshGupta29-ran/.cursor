# VARIANT v32_csharp_enterprise-buyer_multi-tenant-isolation - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `csharp`
- **user_persona**: `enterprise_buyer`
- **novelty_hook**: `multi_tenant_isolation`
- **ui_surface**: `dashboard_charts`
- **persistence**: `json_file`
- **complexity**: `low`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `csharp`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v32_csharp_enterprise-buyer_multi-tenant-isolation`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v32_csharp_enterprise-buyer_multi-tenant-isolation` when demoable.

---

## BASE PRD (honor unless mutated above)

# Brineglass Beacon — Collectible Card Battler (C++17 + HTML Canvas)

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `cpp`
- **ui_surface:** `html_canvas`
- **persistence:** `json_file`
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

## 1. Project request / product identity
Build **Brineglass Beacon**, a single-player collectible card battler. Fantasy: two rival lighthouse keepers duel across a night reef, spending **Lumen** (mana) to summon sea **Allies** and cast **Signals** until one beacon's **Integrity** falls from 20 to 0. A **C++17 backend owns 100% of the rules** and serves a static **HTML Canvas** client; match state persists to **JSON files**. One command (`./run.sh`) builds and serves everything on `localhost:8080`.

Domain lexicon (use everywhere; no generic card-game copy): Lumen refills each turn with +1 max (cap 8); Allies arrive "swamped" (no attack that turn) unless **Surge**; **Shelled** = taunt; **Undertow** = escalating fatigue damage (1,2,3…) when drawing from an empty deck.

## 2. Target users & jobs-to-be-done
- A solo player wanting a 5–10 minute tactical duel in the browser, zero install.
- A staff-engineer maintainer who wants the rules engine separable from transport and verifiable headless — correctness must not require a browser.

## 3. Core entities
- **Card**: id, name, cost, kind (Ally|Signal), atk/hp, keyword (none|Shelled|Surge), rules text, flavor line.
- **Card pool**: ≥14 distinct cards in `data/cards.json`; content is data, not code.
- **Decks**: two preconstructed 30-card decks in `data/decks.json` — *Gullrigger* (low curve, aggressive) and *Reefwarden* (Shelled-heavy, controlling). Player picks one; the AI takes the other.
- **Player state**: integrity, max/current lumen, hand, board (≤5 Allies), deck, undertow counter.
- **Match**: turn number, active player, rng seed, action log, idempotency ledger.
- **Actions**: `play_card`, `attack`, `end_turn` — the only legal state mutations.

## 4. Major feature areas
- **Deterministic rules engine** (pure C++, no I/O): seeded RNG used only for the opening shuffle; same seed + same action sequence ⇒ identical match. Every applied action is appended to the log.
- **Turn structure**: Start (max lumen +1 to cap 8, refill, draw 1 / Undertow), Main (play, attack), End. Combat: attacker targets an enemy Ally or the enemy beacon; **Shelled Allies must be attacked first**; Ally-vs-Ally damage is simultaneous; dead Allies leave the board.
- **AI opponent "The Warden"** (a real algorithm, not random): greedy heuristic with lethal check — enumerate legal actions, score each (lethal-now = top priority; favorable trades; damage per lumen; avoid dumping the hand), apply the best, repeat until only `end_turn` remains. Difficulty: *Normal* runs full scoring; *Easy* skips lethal detection and holds back its costliest playable card. Document the scoring function in `DESIGN.md`. The Warden must never emit an illegal action.
- **Chaos toggle — "Lantern Flicker"** (setting or `?chaos=1`): the server fails ~15% of `POST /api/match/action` calls with `503` + error envelope **before** mutating anything. Every action carries a client-generated idempotency key; a repeated key replays the stored response instead of double-applying. Client auto-retries (≤3, small backoff) and shows a "Lantern flickering…" indicator. The match stays completable and the save uncorrupted.
- **Persistence**: after every applied action, atomically write `data/match.json` (temp file + rename). On match end, update `data/stats.json` (wins, losses, streak). `data/settings.json` holds difficulty + chaos. Boot with an unfinished match ⇒ menu offers **Resume**.
- **Canvas client**: everything game-visible is drawn on one `<canvas>` — both boards, hand, lumen gems, integrity dials, End Turn button, scrolling log strip, hover tooltips, select-then-target with a drawn arrow, win/lose overlay with Rematch. DOM only for the page shell and a controls hint.

## 5. Workflows
**Happy path:** `./run.sh` → open `localhost:8080` → menu (deck, difficulty, chaos) → alternate turns; Warden's plays appear in the log → integrity hits 0 → result screen → stats persist → rematch.
**Edge cases:** Undertow escalation on deck-out; full board (5) blocks summoning with a clear reason; illegal action ⇒ `409` + reason, state untouched; browser refresh mid-match ⇒ state reloaded; server restart mid-match ⇒ Resume works; chaos 503 bursts ⇒ retries recover with no duplicate plays; malformed bodies rejected cleanly.

## 6. Data & persistence
JSON files only: `cards.json`, `decks.json`, `match.json` (autosave, atomic, `"v":1` schema tag), `stats.json`, `settings.json`. The API redacts the AI's hand contents (count only) — no hidden-info leaks.

## 7. UX / API surface
`GET /` (shell+JS) · `POST /api/match/new` · `GET /api/match/state` (redacted) · `POST /api/match/action` (idempotency key required) · `POST /api/match/resume` · `GET|POST /api/settings` · `GET /api/stats`. Board readable at 1024×768; controls discoverable without opening the README.

## 8. Quality, security, reliability
- No runtime network calls; vendored single-header HTTP server and test framework are acceptable — builds need only a C++17 compiler (cmake or one g++ line).
- Server validates every action through the engine; never trust client-side lumen/integrity math.
- Engine invariants: lumen ≥ 0, board ≤ 5, each Ally attacks ≤1×/turn, Shelled targeting enforced, Undertow increments exactly once per empty draw.

## 9. Documentation & testing
- `README.md`: one-command run, controls, rules summary, repo map. `DESIGN.md`: turn loop, Warden scoring, Lantern Flicker recovery design, known limitations.
- **Unit tests** (engine only, no GUI): lumen curve, combat incl. Shelled and simultaneous death, Undertow, seeded-shuffle determinism, save/load roundtrip, idempotent replay, Warden legality sweep across ≥100 seeded states.
- **Smoke test** `tools/smoke.sh`: boots the server, drives a full match to victory via the API, asserts save + stats files, then replays a full match with chaos on and asserts completion; kills the server. Fully headless.

## 10. Constraints & non-goals
- Backend C++17 only; no Node/Python game logic, no WASM. Frontend JS talks to the API only.
- No deck builder, collection/economy, multiplayer, audio, or external art (canvas-drawn glyphs and typography only).
- ~25-minute agent budget: cut features before cutting invariants.

## 11. Acceptance criteria
- [ ] `./run.sh` builds and serves a match playable end-to-end.
- [ ] Draw/lumen/turn rules, Shelled, Surge, and Undertow behave as specified.
- [ ] Warden completes turns using only legal actions on both difficulties.
- [ ] Win and defeat reach a result screen; stats persist across restarts.
- [ ] Mid-match refresh and server restart both resume correctly from `match.json`.
- [ ] Lantern Flicker on: 503s occur, auto-retry recovers, no action double-applies, match completes.
- [ ] Unit tests pass; `tools/smoke.sh` passes headless.
- [ ] README gets a first-time player into a match in under a minute.

## 12. Uniqueness / anti-clone
Not a Hearthstone/Magic reskin: all UI copy, card names, and flavor use the keeper/tide lexicon. Forbidden: placeholder cards ("Card 1"), lorem ipsum, debug-rectangle UI, an "AI" that picks random actions, and a chaos toggle that is wired but never actually fails.
