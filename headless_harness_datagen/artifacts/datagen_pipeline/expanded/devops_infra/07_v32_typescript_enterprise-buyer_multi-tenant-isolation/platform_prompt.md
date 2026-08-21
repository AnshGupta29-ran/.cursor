# VARIANT v32_typescript_enterprise-buyer_multi-tenant-isolation - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `typescript`
- **user_persona**: `enterprise_buyer`
- **novelty_hook**: `multi_tenant_isolation`
- **ui_surface**: `dashboard_charts`
- **persistence**: `json_file`
- **complexity**: `hard`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `typescript`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v32_typescript_enterprise-buyer_multi-tenant-isolation`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v32_typescript_enterprise-buyer_multi-tenant-isolation` when demoable.

---

## BASE PRD (honor unless mutated above)

# ParityPane — keyboard-first `.env` drift console

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `javascript`
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


## 1. Project request / product identity
Build **ParityPane**: a local, fully offline console for release engineers at security-conscious enterprises who must prove environment variables match across `dev` / `staging` / `prod` before a deploy — without pasting secrets into a hosted diff SaaS. It ingests `.env` snapshots, renders a **redacted drift report**, and composes minimal **patches** to bring a target environment to parity.

- **Stack (locked):** vanilla JavaScript, Node ≥ 18, ES modules, **zero required npm dependencies**, no build step. Low complexity: ≤ 10 source files.
- **Delivery (locked):** CLI entry + UI. `bin/paritypane.mjs` serves the console over localhost and opens it in a dedicated desktop app window (Chrome/Edge `--app=` mode; Electron only if already installed — never a required install). The same static files must run standalone in any browser tab for smoke verification.
- **Persistence (locked):** browser `localStorage` (namespaced `paritypane:*`) is the system of record. No server-side DB. No telemetry, no network egress beyond localhost — this is the enterprise buying argument; state it in the README.

## 2. Target users & jobs-to-be-done
- **Release engineer:** "Show me which keys drifted between staging and prod — masked — and let me promote only the safe ones."
- **Security reviewer:** "Prove secrets never render in plaintext by default and that every reveal/apply is audit-logged."
- **Keyboard-driven operator:** complete the entire inspect → patch flow without touching a mouse.

## 3. Core entities
- `EnvironmentSnapshot { id, name, importedAt, sourceLabel, entries[] }`
- `EnvEntry { key, value, isSecret, fingerprint, line, warnings[] }`
- `DiffRow { key, status: same|changed|added|removed|empty, baseFp?, targetFp? }`
- `PatchOp { op: set|delete, key, value? }`
- `AuditEvent { ts, action, detail }` — import, reveal, diff, patch-apply, wipe
- `Settings { redactionMode: mask|last4|fingerprint, extraSecretPatterns[] }`

## 4. Major feature areas
- **Ingest:** paste box, multi-file picker, or CLI preload (`--env prod=.env.prod`, injected via a localhost seed endpoint and merged into localStorage on load). Parser handles comments, `export ` prefix, single/double quotes, blank lines, CRLF; duplicate keys → last wins + warning; malformed lines are listed, never fatal.
- **Secret detection & redaction:** key-name heuristics (`KEY|TOKEN|SECRET|PASS|PWD|CRED`) plus high-entropy value check; three redaction modes; SHA-256 fingerprint (first 10 hex via SubtleCrypto) so reviewers confirm equality without seeing values. Reveal is per-session, keyboard-gated (`R` on focused row), auto re-masks on window blur, and writes an AuditEvent.
- **Drift report:** pick base + target snapshots; grid of DiffRows with status chips; filter by status and substring; summary widgets (counts per status, missing-secret count, duplicate-key warnings).
- **Patch composer:** select rows with `Space` → masked unified-style preview → explicit confirmation → apply mutates the target snapshot in localStorage; dry-run summary line ("3 keys set, 1 removed on prod"); export patch as `.env` snippet or JSON ops.
- **Audit log:** reverse-chronological view (cap 200 events), export as JSON, and a **Lock & wipe** control that clears all `paritypane:*` keys.

## 5. Domain workflows
**Happy path:** `node bin/paritypane.mjs --env staging=fixtures/staging.env --env prod=fixtures/prod.env` → app window opens with both snapshots preloaded → operator tabs to env pickers → drift grid populates with an `aria-live` announcement → arrows navigate rows, `Space` selects changed keys → `P` opens patch preview → `Enter` confirms → success announced → audit log records the apply.

**Edge cases:** empty file → empty state with import hints; identical envs → "at parity" state; key present with empty value flagged `empty`; duplicate keys and malformed lines surface as warnings; localStorage quota failure → non-blocking toast; unknown CLI flags → non-zero exit with usage.

## 6. Data & persistence
Snapshots, settings, and audit log live only in localStorage. The CLI is stateless. README must document the threat model (plaintext secrets persist in localStorage until wipe) and the wipe control.

## 7. UX surface expectations
Accessibility-first keyboard UX is the product's signature and is non-negotiable: every feature operable by keyboard; `?` opens a shortcut cheatsheet dialog; `Cmd/Ctrl+K` command palette; drift grid uses roving tabindex with `role="grid"`; dialogs trap and restore focus; visible focus rings; `aria-live="polite"` for async results; `prefers-reduced-motion` respected; masked values carry screen-reader labels ("redacted, 18 chars, fp 9f2…"). Status color semantics documented in README (never color-only — pair with chips/text).

## 8. Quality, security, reliability
No external requests (CSP meta tag); no `eval`; secrets never present in initial HTML; confirmation before any overwrite-apply; parser never throws on garbage input; pure logic modules (`envparse`, `diff`, `redact`, `patch`) shared between browser, CLI, and tests.

## 9. Documentation & testing
README: prerequisites (Node 18+), quickstart, full shortcut map, redaction/threat model, demo script. Tests: `node --test` integration-light coverage of the messy-legacy fixture parsing, drift status computation, fingerprint stability, and patch-apply semantics. Smoke: `npm run smoke` boots the CLI server on an ephemeral port and asserts `/`, `/app.js`, and `/api/seed` respond and that index.html contains the mount node.

## 10. Constraints & non-goals
Not a secrets manager or vault; no writing arbitrary disk files from the UI; no git integration; no multi-user; no frameworks, bundlers, puppeteer, or native builds; never require Electron.

## 11. Acceptance criteria
- [ ] CLI preloads two `--env` files and opens the console window; snapshots persist in localStorage
- [ ] Drift grid shows same/changed/added/removed/empty with masked values + fingerprints
- [ ] Three operator actions work keyboard-only: reveal (`R`), select (`Space`), patch apply (`P` → confirm → `Enter`)
- [ ] Patch apply requires confirmation and writes an AuditEvent; plaintext never renders by default; reveal re-masks on blur
- [ ] `fixtures/legacy-messy.env` (duplicates, `export`, quotes, inline comments, CRLF, malformed lines) parses with warnings, no crash
- [ ] `node --test` and `npm run smoke` pass; `?` cheatsheet and command palette work
- [ ] README demo script and threat model included

## 12. Uniqueness / anti-clone constraints
Must use env-parity domain language (drift, fingerprint, promote, parity, snapshot). Reject: generic file-diff tools, pastebins, todo-style CRUD, plaintext-by-default secret displays, placeholder UIs, and any outbound network call. The fixtures must be realistic environment files (database URLs, API tokens, feature flags), not lorem ipsum.
