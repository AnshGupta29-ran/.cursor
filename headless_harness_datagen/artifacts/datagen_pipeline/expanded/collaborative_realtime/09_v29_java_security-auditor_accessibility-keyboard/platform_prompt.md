# VARIANT v29_java_security-auditor_accessibility-keyboard - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `java`
- **user_persona**: `security_auditor`
- **novelty_hook**: `accessibility_keyboard`
- **ui_surface**: `desktop_window`
- **persistence**: `localstorage`
- **complexity**: `medium`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `java`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v29_java_security-auditor_accessibility-keyboard`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v29_java_security-auditor_accessibility-keyboard` when demoable.

---

## BASE PRD (honor unless mutated above)

# ReconGrid — Local-First Collaborative CSV Reconciliation Grid

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `typescript`
- **ui_surface:** `desktop_window`
- **persistence:** `localstorage`
- **complexity:** `low`
- Do **not** rewrite this project in a different language.

## Complexity & fidelity lock (datagen)
- Complexity band: **low**
- UI fidelity: LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form
- Effort cue: typically thinner than medium/hard (fewer files & screens), but never stop early
- Anti-stub: FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.
- **Build-first (anti time-waste):** Implement immediately from this PRD. Forbidden: WebSearch/WebFetch, browsing docs sites, winget/ripgrep installs for searching, Explore/research subagents, Grep/Glob fishing across sibling tasks. At most 2 targeted reads inside this task workdir before Write/Edit. Low = few files shipped fast — do not gold-plate.


## 1. Project Request / Product Identity
**ReconGrid** is a keyboard-first, multi-window collaborative spreadsheet for reconciling CSV extracts. Two analysts open the same session in separate desktop browser windows; every committed cell edit appears in the peer window in near real time, and simultaneous edits to the same cell are surfaced as **disputes** to resolve — never silently overwritten.

- **One-sentence pitch:** "Pair-reconcile vendor CSVs in the browser with live sync, cell-level dispute flagging, and an exportable audit trail — no SaaS, no server database, data never leaves the machine."
- **Buyer lens (enterprise):** zero external data egress, seat-free local demo, auditable conflict history, CSV round-trip fidelity.
- **Domain twist:** reconciliation workflow — conflicts are first-class *disputes* with keep-mine / take-theirs resolution and a session audit log a controller can export.
- **Stack (locked):** TypeScript (Vite, vanilla TS — no framework), desktop browser window, `localStorage` persistence, thin CLI entry. Target: runnable in <10 minutes of build work.

## 2. Target Users & Jobs-to-be-Done
- **Ops/finance analyst pair** reconciling a vendor invoice extract against a baseline.
  - "We edit the same grid from two windows and see each other's fixes live."
  - "If we both touched a cell, I want it flagged and resolvable without a mouse."
  - "I export the reconciled CSV and the dispute log for sign-off."

## 3. Core Requirements / Entities
Materialize these (names flexible, substance not):
- **Session** (join code, owner id, created-at) — the collaboration space.
- **Participant** (display name, role: `owner | editor | viewer`, color chip, last-seen).
- **GridDoc** (headers, rows; all values strings; current committed state).
- **CellCommit** (event: row, col, old, new, author, timestamp) — capped audit log (last 200).
- **Dispute** (cell ref, mine value, theirs value, authors, status open/resolved).
- **PresencePing** (participant id, focused cell, idle flag).

## 4. Major Feature Areas
- **Sessions & membership:** create session → get 4–6 char code; join by code. First joiner is owner; subsequent joiners pick editor or viewer. Soft cap 6 participants; overflow joins as viewer. Identity persists across refresh (stored participant id).
- **Presence:** participant roster with color chips; each peer's focused cell outlined in their color; idle marking via `visibilitychange`; status pill: `Live · N participants` / `Solo — open another window with code XXXX`.
- **Cell editing & live sync:** click or Enter/F2 edits; Tab commits+moves; Esc cancels. Transport = `BroadcastChannel` per session code with `storage`-event fallback; `localStorage` is the durable authority. Commits apply optimistically locally and broadcast.
- **Disputes (conflict policy — pick and implement exactly):** committed state is **last-write-wins**, BUT a Dispute is opened when (a) a remote commit lands on a cell with an uncommitted local edit, or (b) two commits to the same cell with different values arrive within 2s. Disputed cells get a striped highlight + badge; resolution (keep-mine / take-theirs) writes a new commit, closes the dispute, and logs it.
- **CSV import/export:** import via file picker or paste (header row required; ragged rows padded with warning). Owner-only; importing while peers edit requires confirmation and broadcasts a doc-reset event. Export produces a faithful round-trip (correct quoting/escaping of commas, quotes, newlines) plus optional `disputes.csv` audit export.
- **Accessibility-first keyboard UX (novelty core):** ARIA `grid` role with roving tabindex; arrow-key navigation; full action set reachable without a mouse; visible focus ring; `aria-live="polite"` announcer narrates remote edits ("Row 4, Amount changed by Priya to 19.40") and new disputes; `Alt+D` jumps to next open dispute; `Ctrl+Z` undoes your last commit; `Ctrl+E` exports. No hover-only or drag-only interactions.

## 5. Domain Workflows
**Happy path:** Owner runs CLI → seeded demo session opens (vendor-invoice fixture) → second window joins by code → both edit cells, see live updates + presence outlines → simultaneous edit on one cell → dispute badge → `Alt+D`, choose take-theirs via keyboard → export reconciled CSV.
**Edge cases:** refresh mid-edit restores doc + identity and discards uncommitted edit; viewer attempts edit → rejected with announcement; BroadcastChannel unavailable → storage-event fallback with "degraded sync" pill; localStorage quota error → non-blocking toast, in-memory state kept; import-during-collaboration resets peers' grids with notice.

## 6. Data & Persistence
`localStorage` only, namespaced: `recongrid:session:<code>:doc | :events | :participants | :me`. State survives refresh; disputes survive until resolved. No server DB, no IndexedDB, no cookies.

## 7. UX / API Surface
- **CLI (`recongrid`):** `recongrid serve [--port N] [--seed demo]` serves the built app and prints the session URL/code; `recongrid --help` documents commands.
- **UI (single desktop window):** session bar (code, role, status pill, roster), grid region, disputes panel (list + resolve buttons, keyboard navigable), announcer live region. Empty state teaches: "Import a CSV or load the demo extract."

## 8. Quality, Security, Reliability
Validate CSV parse + join codes; debounce presence pings (~300ms); cap audit log; escape all cell content on render (no HTML injection); graceful messaging when sync is degraded.

## 9. Documentation & Testing
- README: run steps (`npm i`, `npm run dev` / CLI), two-window demo script, architecture note explaining BroadcastChannel + localStorage authority + fallback.
- **Integration-light tests (required, vitest + jsdom):** CSV round-trip; dispute policy (cases a & b); role gate (viewer edit rejected); two simulated clients sharing a storage/bus shim converge on the same doc.
- **Browser smoke (required):** `npm run smoke` — Playwright (chromium only) opens two windows on one session, edits a cell in A, asserts visibility in B, triggers and resolves a dispute, reloads and asserts persistence.

## 10. Constraints & Non-Goals
Not an Excel/Sheets plugin, no formulas, no formatting engine, no charts, no server/WebSocket backend, no auth beyond session code + role pick, no mobile layout work, no multi-doc accounts.

## 11. Acceptance Criteria
- [ ] Two windows join one session by code; edits sync without reload
- [ ] Simultaneous same-cell edit opens a dispute; keyboard-only resolution works
- [ ] Refresh restores grid, disputes, and identity
- [ ] Viewer role blocked from editing (tested)
- [ ] CSV export round-trips the demo fixture byte-faithfully
- [ ] Every primary action operable by keyboard; remote changes announced via live region
- [ ] Integration tests + browser smoke pass; README demo script accurate

## 12. Uniqueness / Anti-Clone Rules
No generic "Sheet1 / A1 / User A" placeholders — ship the seeded **vendor-invoice reconciliation fixture** (vendor, invoice #, PO match status, amount, variance, notes). UI copy must use reconciliation language (dispute, baseline, variance, sign-off), not chat/whiteboard terms. No Socket.IO whiteboard/chat clones; the dispute-resolution workflow and keyboard-first ARIA grid are mandatory differentiators, not optional polish.
