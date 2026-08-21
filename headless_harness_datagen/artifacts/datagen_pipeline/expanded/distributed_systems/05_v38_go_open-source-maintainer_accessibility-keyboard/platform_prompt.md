# VARIANT v38_go_open-source-maintainer_accessibility-keyboard - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `go`
- **user_persona**: `open_source_maintainer`
- **novelty_hook**: `accessibility_keyboard`
- **ui_surface**: `mobile_web`
- **persistence**: `csv_files`
- **complexity**: `hard`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `go`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v38_go_open-source-maintainer_accessibility-keyboard`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v38_go_open-source-maintainer_accessibility-keyboard` when demoable.

---

## BASE PRD (honor unless mutated above)

# PlainTally — Keyboard-First Mini MapReduce Word-Frequency Auditor

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `csharp`
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


## 1. Project Request / Product identity
PlainTally is a single-machine C# (.NET 8) miniature MapReduce engine for enterprise content-governance teams. It ingests a folder of `.txt`/`.md` policy documents, splits them into chunks, runs concurrent map workers that tokenize words, shuffles by hash partition, reduces to global term frequencies, and merges a ranked report with CSV export. Differentiator: an accessibility-first **desktop window** where the entire pipeline is operable and perceivable by keyboard alone — procurement-ready for WCAG 2.2 AA / Section 508 programs. Dual delivery: CLI entry (`plaintally run <folder>`) for scripted audits, and a desktop UI for analysts. Thin MVP: few files, minimal polish, runnable demo.

## 2. Target users & jobs-to-be-done
- **Compliance/content-governance lead (enterprise buyer):** prove plain-language adherence across a corpus without sending data to any cloud service — everything runs locally.
- **Accessibility-minded analyst:** run an audit, inspect dead-lettered chunks, and export results using keyboard + screen reader only.
Jobs: "Audit this folder into a ranked term/jargon frequency report." "Show which chunks failed and why." "Re-run after fixes, keeping an auditable local history."

## 3. Core requirements / entities
- `AuditJob`: id, source folder, status vocabulary: `Queued → Splitting → Mapping → Shuffling → Reducing → Merging → Succeeded | Failed | PartialWithDeadLetters | Cancelled`.
- `ChunkTask`: map unit (file + byte range), attempts, lease with visibility timeout (~5s).
- `TaskAttempt`: worker id, start/end, outcome, error.
- `Worker`: id, heartbeat timestamp, concurrency cap (default 2; demo must show ≥2), state `Idle|Busy|Lost`.
- `ShufflePartition`: hash bucket of word → partial counts (R=4).
- `DeadLetter`: chunk that exhausted attempts, with last error.
- `JobRecord`: persisted summary (top-N terms, dead letters, counts) in browser localStorage.
Engine state is in-memory during a run; durable artifacts live in localStorage (§6).

## 4. Major feature areas
- **Splitter:** enumerate files; split into ~64KB chunks aligned to line boundaries (never mid-line).
- **Scheduler:** priority FIFO; assigns tasks to workers; stale-heartbeat tasks are re-leased after the visibility timeout; per-worker concurrency limit.
- **Map workers:** thread-pool tasks; tokenize (lowercase, strip punctuation), emit `(word,1)`; heartbeat every 500ms; liveness detection marks workers `Lost`.
- **Shuffle/reduce:** hash partitions; reducers sum counts. Delivery claim (document): **at-least-once** task execution with idempotent, commutative aggregation.
- **Reliability:** exponential backoff + jitter (base 200ms, ×2, ±50% jitter), max 3 attempts → DeadLetter; job ends `PartialWithDeadLetters` if DL non-empty.
- **Merge:** deterministic sort (count desc, word asc); export top-1000 CSV.
- **Chaos toggle:** injects ~25% random map-task failures to demonstrate retries/DLQ.
- **Observability:** metrics strip (queue depth, in-flight, succeeded, failed, retried, dead-lettered); structured JSON-lines log pane; graceful stop finishes the current chunk then requeues.
- **CLI:** `plaintally run <folder> [--chaos] [--workers N]` prints JSON summary + writes CSV; `plaintally ui` opens the window.

## 5. Domain-specific workflows
**Happy path:** open window → Ctrl+O picks folder → Ctrl+Enter starts → live region announces each stage → results grid receives focus → arrow keys browse terms → Enter shows per-document counts → Ctrl+E exports CSV.
**Edge cases:** empty folder (clear empty state); unreadable/binary file (chunk retries → dead-letter, job still merges surviving data); worker killed mid-task (lease expiry requeues, nothing lost); duplicate execution after retry (counts stay correct — verify against fixture with known counts); Stop mid-run (in-flight chunk completes, rest requeue, job recorded `Cancelled`).

## 6. Data & persistence expectations
localStorage keys (prefix `plaintally.`): `jobs` (last 20 JobRecords incl. dead letters), `lastReport` (merged top-N + CSV text), `prefs` (contrast, reduced motion, shortcuts dismissed). Closing/reopening the window must restore history, last report, and preferences. Include a "Clear local history" action. No servers, databases, or cloud.

## 7. UX / API surface expectations
Desktop window — suggest Photino.NET hosting one `web/index.html`; **the same file must open standalone in a browser with demo data** so it passes a browser smoke test without the backend. Keyboard-complete:
- Logical tab order, always-visible focus ring, skip-to-results link.
- Results as a real grid: arrow-key navigation, Enter opens term detail.
- `aria-live="polite"` announcer for stage/metric changes; progressbar roles on stage meters.
- Shortcut palette on `?` (Ctrl+O, Ctrl+Enter, Ctrl+E, Ctrl+L logs, Ctrl+Shift+X chaos).
- Honor `prefers-reduced-motion`; persisted high-contrast toggle; ≥4.5:1 text contrast.
- Domain vocabulary on screen: chunks, partitions, leases, dead letters — never generic "items".

## 8. Quality, security, reliability
Local-only; path validation confines reads to the selected folder; skip files >10MB with notice. No lost chunks on clean stop; retries never double-count (integration-verified). Structured logs; no PII leaves the machine.

## 9. Documentation & testing
README: .NET 8 install, CLI demo, UI demo, failure-injection walkthrough (enable chaos / kill a worker → observe backoff + DLQ), delivery-semantics section (at-least-once + idempotent reduce), full keyboard map. Tests (light integration, xUnit): (a) ≥2 workers process a fixture corpus and merged counts match a hand-computed baseline; (b) a failing worker produces backoff bookkeeping and dead-letter after max attempts. Browser smoke checklist: open `index.html` standalone; verify render, live-region announcements on demo data, and a complete keyboard loop.

## 10. Constraints & non-goals
Not Hadoop/Spark; single machine, simulated distribution via threads; no network RPC, external services, or heavy dependencies. Few files: one small engine project, one UI host, one HTML page, one test file. No sleeping-only fake workers — tasks must do real tokenization.

## 11. Acceptance criteria
- [ ] CLI audits a folder and prints correct JSON + CSV.
- [ ] Desktop window runs the full pipeline; ≥2 workers visibly process concurrently.
- [ ] Chaos mode yields retries with backoff+jitter; exhausted tasks land in dead-letter; job reports `PartialWithDeadLetters`.
- [ ] Worker heartbeat loss is detected; its chunk is re-leased without loss.
- [ ] Window restart restores history/report/prefs from localStorage.
- [ ] Every UI action is keyboard-reachable; stage changes announced via live region.
- [ ] Integration tests pass; `index.html` passes standalone browser smoke.
- [ ] README demo + semantics section complete.

## 12. Uniqueness / anti-clone constraints
Forbidden: generic todo/CRUD scaffolding, "hello queue" boilerplate, placeholder tables, lorem-ipsum corpora. Must use MapReduce/audit terminology (chunks, shuffle partitions, leases, dead letters, jargon density). Fixture corpus must be plausible policy documents (`travel-policy.md`, `security-handbook.txt`, …) with a hand-computable word baseline. Accessibility-first keyboard UX is a hard feature, not a nicety.
