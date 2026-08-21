# VARIANT v33_typescript_open-source-maintainer_dark-ops-console - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `typescript`
- **user_persona**: `open_source_maintainer`
- **novelty_hook**: `dark_ops_console`
- **ui_surface**: `static_html`
- **persistence**: `csv_files`
- **complexity**: `medium`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `typescript`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v33_typescript_open-source-maintainer_dark-ops-console`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v33_typescript_open-source-maintainer_dark-ops-console` when demoable.

---

## BASE PRD (honor unless mutated above)

# Trainyard — Merge-Train Code Review Console

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `typescript`
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


## 1. Project Request / Product identity
Build **Trainyard**, a TypeScript web platform where a small platform team reviews code and dispatches merges through a **merge train**. It combines repository browsing, issues, pull requests, approvals, and Markdown rendering with a live **ops deck**: a continuously re-rendering "rail yard" window (game-loop style render tick + polled state) showing train slots, signal states, and an audit event ticker. Persistence is **SQLite**. A first-class **chaos toggle** injects one recoverable failure (signal fault) into the train so operators can drill recovery. Audience is staff engineers: be terse, explicit about invariants, no toy UI.

## 2. Target users & primary jobs-to-be-done
- **Maintainer**: triage issues/PRs, approve reviews, board the train, recover blocked slots.
- **Viewer** (read-only): browse repos, watch the deck.
Jobs: "see everything about to land at a glance", "gate merges on approval", "recover from a flaky check with zero data loss".

## 3. Core entities (SQLite)
- `Operator(id, handle, password_hash /* scrypt */, role: maintainer|viewer)`
- `Repository(id, slug, name, description, default_branch)`
- `RepoFile(repo_id, branch, path, content, updated_at)` — virtual tree, seeded fixtures; **no git shelling**
- `Issue(id, repo_id, number, title, body_md, status: open|closed, author_id, created_at)`
- `PullRequest(id, repo_id, number, title, body_md, source_branch, target_branch, status: OPEN|MERGED|CLOSED, author_id)`
- `Review(pr_id, operator_id, state: APPROVED|CHANGES_REQUESTED, UNIQUE(pr_id, operator_id))`
- `MergeSlot(id, pr_id, position, state: QUEUED|CHECKING|DISPATCHED|BLOCKED_RECOVERABLE, attempts, last_error)`
- `Comment(id, target_type: issue|pr, target_id, author_id, body_md, created_at)`
- `AuditEvent(id, actor, action, target, payload_json, created_at)` — append-only
- `ChaosFlag(id=1, enabled, updated_by)`

## 4. Major feature areas
- **Auth**: register/login/logout/me; scrypt+salt hashing; HttpOnly `SameSite=Lax` session cookie; viewers get 403 on any mutation. First registered operator becomes maintainer.
- **Repo browsing**: repo list; per-repo file tree (flat path list acceptable) and file content view; default branch only.
- **Issues**: list (filter open/closed, search title), create, close/reopen, comment; Markdown bodies.
- **Pull requests**: list/create/close; detail shows body, reviews, train state. Reviews: approve / request-changes (upsert per operator).
- **Merge train**: enqueue PR (approval-gated); a server tick (~2s) advances slots FIFO: `QUEUED→CHECKING→DISPATCHED`, then marks the PR `MERGED`. Retry endpoint for blocked slots.
- **Chaos toggle**: maintainer-only `POST /api/chaos {enabled}`. While enabled, each `CHECKING` transition has probability `p` (env `CHAOS_P`, default 0.5, injectable in tests) to land in `BLOCKED_RECOVERABLE` with `SIGNAL_FAULT`. Retry re-enters `CHECKING`. Failure is recoverable: no partial merges, transitions transactional.
- **Markdown**: render issue/PR/comment bodies server-side with a small MD library; sanitize output (strip scripts/`on*` attrs); store raw MD.
- **Audit**: every mutation writes an `AuditEvent`; deck ticker streams the tail.

## 5. Domain workflows
**Happy path**: register → seeded repos present → open PR → a second maintainer approves → enqueue → deck animates slot through signals → `DISPATCHED` → PR `MERGED`; audit events stream.
**Edge cases**: author self-approval → 409; enqueue without ≥1 non-author `APPROVED` → 409; open `CHANGES_REQUESTED` blocks enqueue until superseded; chaos fault → amber signal + retry succeeds; DB write failure → 500 surfaced, slot state unchanged; ≥3 consecutive poll failures → `STALE` banner while UI keeps rendering last snapshot.

## 6. Data & persistence
SQLite file (`data/trainyard.db`) via `better-sqlite3` or equivalent; WAL mode; schema + seed auto-applied on boot when empty (2 repos, ~12 files, 3 issues, 2 PRs, one maintainer + one viewer demo account documented in README). Indexes on `(repo_id, number)` for issues/PRs and `MergeSlot(position)`. Audit reads capped (`LIMIT 200`).

## 7. UX / API surface expectations
Single-page deck (Vite + TypeScript; React optional). **Game loop**: poll `GET /api/deck` (aggregate snapshot: train slots, signal states, counts, audit tail) every 2s; `requestAnimationFrame` render tick animates slot movement and signal blink; interaction via clickable panels and a PR detail drawer — functional console, not a fake game. Panels: **Yard** (train), **Repos**, **Issues**, **PR detail**, **Event ticker**. Rail-yard terminology in labels ("Dispatch", "Signal", "Blocked — Retry"). Destructive actions (close PR, dequeue slot) require a confirm dialog. REST JSON under `/api/*`; consistent error shape `{error, code}`; correct 401/403/409/422 semantics.

## 8. Quality, security, reliability
All train state changes in transactions. **Invariant: a PR is `MERGED` iff its slot reached `DISPATCHED`.** Sanitized Markdown (XSS test mandatory). No shelling to git or arbitrary system commands. Deck snapshot must avoid N+1 queries. In-memory throttle on login. Chaos RNG injectable for deterministic tests.

## 9. Documentation & testing
README: one-command quickstart (`npm install && npm run dev` → single port, schema+seed automatic), demo script (inspect → approve → board → chaos on → recover → merged), roles/accounts, chaos design note, API summary. Tests (Vitest): **unit** — scrypt verify, approval gate, chaos injector with forced RNG, Markdown sanitizer, FIFO ordering; **smoke** — boot server on ephemeral port, drive the full happy path including chaos recovery over HTTP, assert final `MERGED` (`npm run smoke`, <30s).

## 10. Constraints & non-goals
No real git, no diffs/patches, no webhooks, no multi-branch browsing, no orgs, no external CI ("checks" are simulated by the train tick). Not a GitHub-clone checklist exercise.

## 11. Acceptance criteria
- [ ] `npm run dev` boots API+UI on one port with schema+seed, zero manual steps
- [ ] Register/login/logout work; viewers cannot mutate (403)
- [ ] Seeded repo tree + file contents browsable
- [ ] Issues create/close/comment with sanitized Markdown
- [ ] PR create/close/review; self-approval and approval-less enqueue rejected (409)
- [ ] Train processes FIFO; PR reaches `MERGED` only via `DISPATCHED`; mutations audited
- [ ] Chaos toggle yields recoverable `BLOCKED_RECOVERABLE`; retry completes the merge with no partial state
- [ ] Deck polls and re-renders live; stale banner on poll failure
- [ ] Unit + smoke suites pass; smoke covers chaos recovery
- [ ] README demo script reproducible as written

## 12. Uniqueness / anti-clone constraints
Merge-train / rail-yard framing and terminology must pervade UI and API — a generic "GitHub clone with extra steps" fails review. The game-loop ops deck is the primary surface; a plain CRUD table UI fails. Chaos toggle is tested, not a stub. No placeholder pages, no `localStorage` persistence, no lorem-ipsum fixtures (seed plausible platform/infra repos). Repo may contain a partial scaffold — reconcile with it, don't blindly overwrite; plan module layout (`server / db / train / ui`) before writing code.
