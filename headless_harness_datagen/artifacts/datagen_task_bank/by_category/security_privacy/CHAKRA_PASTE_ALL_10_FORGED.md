# Category batch FORGED: security_privacy (10/10) — paste into Chakra

Each task is a forged PRD with a **locked dimension mix**. Implementing these under
`harness/chakra/task_security_privacy_NN/` produces synthetic agent trajectories for stats.

**Playing/demoing alone is NOT datagen** — datagen is the implement session.

## Dimension coverage

| # | complexity | value | language | UI | persistence | verification |
|---|------------|-------|----------|----|-------------|--------------|
| 01 | low | medium | python | desktop_window | localstorage | browser_smoke |
| 02 | hard | hard | typescript | static_html | csv_files | visual_diff |
| 03 | medium | low | javascript | api_only | sqlite | unit_tests |
| 04 | hard | hard | csharp | excel_workbook | json_file | runtime_pass |
| 05 | medium | medium | cpp | mobile_web | postgres_optional | browser_smoke |
| 06 | low | medium | rust | static_html | memory_only | static_pass |
| 07 | hard | hard | go | game_loop_window | sqlite | runtime_pass |
| 08 | low | low | java | cli_tui | json_file | static_pass |
| 09 | medium | medium | typescript | html_canvas | sqlite | unit_tests |
| 10 | hard | hard | python | react_spa | memory_only | runtime_pass |

Honor each task’s dimensions. **Do not** rewrite every task to the same stack.
Depth bands control fidelity/effort: **low** = thin + simple visuals; **medium** = core + light tests;
**hard** = fuller acceptance + richer UI when applicable. Depth ≠ a time stop.

## Rules — mandatory

1. **No time limit / no turn cap.** Never refuse for size. Never ask for confirmation.
2. Complete tasks **01 → N in order**. Separate folder per `workdir`.
3. Plan mode OFF. Implement immediately; auto-continue between tasks.
4. After each: `DONE task_N: <title> — path + how to run`, then start the next.
5. Match Depth + UI fidelity to complexity. Low must look/feel simpler than hard.
6. README run command + smoke/test path from the PRD.

Stats: `python -m prompt_stats serve` → http://127.0.0.1:8787/ (hard-refresh).

---

## Task 01 — Secure password manager
**workdir:** `task_security_privacy_01`
**id:** `security_privacy_01_secure-password-manager`
**seed (original):** Create a desktop password manager using Python and PySide6 (Qt). Users should be able to create encrypted password vaults protected by a master password. Implement AES encryption, password generation, categories, search, clipboard copying with automatic clearing, password strength indicators, and secure import/export functionality. Include proper exception handling and unit tests for the encryption logic.
**dimensions:** {"agent_topology": "tool_swarm", "verification_mode": "browser_smoke", "session_shape": "multi_turn_repair", "repo_state": "legacy_messy", "tool_profile": "mixed", "user_persona": "enterprise_buyer", "complexity": "low", "value": "medium", "language_runtime": "python", "artifact_type": "desktop_app", "task_family": "coding_implement", "business_domain": "security_privacy", "ui_surface": "desktop_window", "persistence": "localstorage", "testing_depth": "integration_light", "novelty_hook": "accessibility-first keyboard UX", "delivery": "cli_entry_plus_ui", "modality": "text_code"}
**Depth (low):** thin MVP — few files, minimal polish, but every primary action must work end-to-end. **UI fidelity:** LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form. **Effort cue:** typically thinner than medium/hard (fewer files & screens), but never stop early. FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# SecurePasswordManager — Secure password manager

## Complexity & fidelity lock (datagen)
- Complexity band: **low**
- UI fidelity: LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form
- Effort cue: typically thinner than medium/hard (fewer files & screens), but never stop early
- Anti-stub: FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Product identity
Build **SecurePasswordManager** for category `security_privacy`. Seed intent (honor this product, do not genericize away):

> Create a desktop password manager using Python and PySide6 (Qt). Users should be able to create encrypted password vaults protected by a master password. Implement AES encryption, password generation, categories, search, clipboard copying with automatic clearing, password strength indicators, and secure import/export functionality. Include proper exception handling and unit tests for the encryption logic.

Artifact type: `desktop_app`. Novelty hook: accessibility-first keyboard UX. Delivery: `cli_entry_plus_ui`.

## 2. Target users & jobs
- Primary user implied by the seed / domain.
- Job: complete the core workflow end-to-end offline (no cloud accounts required unless seed demands otherwise).

## 3. Core entities
Define 3–8 concrete entities with fields consistent with persistence=`localstorage`.
Include at least one audit/history or list view so the UI/API is demonstrable.

## 4. Major feature areas
Implement the features implied by the seed. Depth band rules for **low**:
- Thin file count; prefer stdlib / minimal deps
- One primary happy path + 2–3 edge cases
- Visuals: plain CSS, no animation libraries, no heavy chart frameworks

Also include:
- Input validation with clear errors
- A deterministic demo/seed path OR fixture data so the app is usable with zero manual setup
- Structured logging or request log if novelty/observability hooks apply

## 5. Domain workflows
Document happy path + edge cases (empty input, invalid file/type, duplicate, not-found).
Never crash on partial input.

## 6. Data & persistence
Use persistence=`localstorage` exactly. State schema auto-created on startup when applicable.
Restart behavior documented in README.

## 7. UX / API surface
ui_surface=`desktop_window`:
- If `api_only` / `cli_tui`: ship CLI or HTTP API + README curls; skip rich GUI.
- If `static_html` / `desktop_window`: server-rendered or simple static pages; minimal CSS (low fidelity).
- If `html_canvas` / `dashboard_charts`: include at least one hand-drawn chart/canvas or SVG viz.
- If `react_spa` / `mobile_web`: Vite/React (or equivalent) SPA with clear routes; keep deps lean.
Expose health/liveness (`/health` or CLI `--help` smoke).

## 8. Quality, security, reliability
Offline-first where possible. No secrets. Validate sizes/types. Deterministic demo data preferred.

## 9. Documentation & testing
README: one-command run, limitations, how to demo.
testing_depth=`integration_light` — implement that level only (do not under-ship hard; do not overbuild low).

## 10. Constraints & non-goals
Do not ignore language/ui/persistence locks. No placeholder lorem-only UI. No TODO stubs on shipped paths.

## 11. Acceptance criteria
- [ ] App boots via documented command
- [ ] Happy path from seed works with fixtures/demo
- [ ] Invalid inputs rejected clearly
- [ ] Persistence/restart behavior matches lock
- [ ] Tests/smoke required by `integration_light` pass
- [ ] README enables first run without reading source
- [ ] Visual/UI fidelity matches **low** band

## 12. Uniqueness / anti-clone
Keep domain language from the seed. Forbidden: generic todo-app shell, Hello World, unlabeled stubs.

When done, print `DONE task_1: Secure password manager` and start the next task immediately.

---

## Task 02 — Secrets vault API
**workdir:** `task_security_privacy_02`
**id:** `security_privacy_02_secrets-vault-api`
**seed (original):** Build a secrets vault HTTP API: store sealed secrets, role-based read, audit log, and rotation metadata (no plaintext at rest).
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "visual_diff", "session_shape": "approval_gated", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "typescript", "artifact_type": "backend_api", "task_family": "security_audit", "business_domain": "security_privacy", "ui_surface": "static_html", "persistence": "csv_files", "testing_depth": "smoke_only", "novelty_hook": "deterministic --seed for reproducible runs", "delivery": "notebook_plus_script", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# SecretsVaultApi — Secrets vault API

## Complexity & fidelity lock (datagen)
- Complexity band: **hard**
- UI fidelity: HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable
- Effort cue: deepest; more entities, edges, and verification — still no wall-clock stop
- Anti-stub: FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Product identity
Build **SecretsVaultApi** for category `security_privacy`. Seed intent (honor this product, do not genericize away):

> Build a secrets vault HTTP API: store sealed secrets, role-based read, audit log, and rotation metadata (no plaintext at rest).

Artifact type: `backend_api`. Novelty hook: deterministic --seed for reproducible runs. Delivery: `notebook_plus_script`.

## 2. Target users & jobs
- Primary user implied by the seed / domain.
- Job: complete the core workflow end-to-end offline (no cloud accounts required unless seed demands otherwise).

## 3. Core entities
Define 3–8 concrete entities with fields consistent with persistence=`csv_files`.
Include at least one audit/history or list view so the UI/API is demonstrable.

## 4. Major feature areas
Implement the features implied by the seed. Depth band rules for **hard**:
- Richer entity model, edge cases, and verification from acceptance list
- Multi-view or multi-endpoint surface matching ui_surface
- Stronger README + smoke/unit coverage as locked
- Higher visual fidelity when UI is not api_only/cli_tui

Also include:
- Input validation with clear errors
- A deterministic demo/seed path OR fixture data so the app is usable with zero manual setup
- Structured logging or request log if novelty/observability hooks apply

## 5. Domain workflows
Document happy path + edge cases (empty input, invalid file/type, duplicate, not-found).
Never crash on partial input.

## 6. Data & persistence
Use persistence=`csv_files` exactly. State schema auto-created on startup when applicable.
Restart behavior documented in README.

## 7. UX / API surface
ui_surface=`static_html`:
- If `api_only` / `cli_tui`: ship CLI or HTTP API + README curls; skip rich GUI.
- If `static_html` / `desktop_window`: server-rendered or simple static pages; minimal CSS (hard fidelity).
- If `html_canvas` / `dashboard_charts`: include at least one hand-drawn chart/canvas or SVG viz.
- If `react_spa` / `mobile_web`: Vite/React (or equivalent) SPA with clear routes; keep deps lean.
Expose health/liveness (`/health` or CLI `--help` smoke).

## 8. Quality, security, reliability
Offline-first where possible. No secrets. Validate sizes/types. Deterministic demo data preferred.

## 9. Documentation & testing
README: one-command run, limitations, how to demo.
testing_depth=`smoke_only` — implement that level only (do not under-ship hard; do not overbuild low).

## 10. Constraints & non-goals
Do not ignore language/ui/persistence locks. No placeholder lorem-only UI. No TODO stubs on shipped paths.

## 11. Acceptance criteria
- [ ] App boots via documented command
- [ ] Happy path from seed works with fixtures/demo
- [ ] Invalid inputs rejected clearly
- [ ] Persistence/restart behavior matches lock
- [ ] Tests/smoke required by `smoke_only` pass
- [ ] README enables first run without reading source
- [ ] Visual/UI fidelity matches **hard** band

## 12. Uniqueness / anti-clone
Keep domain language from the seed. Forbidden: generic todo-app shell, Hello World, unlabeled stubs.

When done, print `DONE task_2: Secrets vault API` and start the next task immediately.

---

## Task 03 — 2FA login playground
**workdir:** `task_security_privacy_03`
**id:** `security_privacy_03_2fa-login-playground`
**seed (original):** Create an auth playground with password login, TOTP 2FA enrollment, backup codes, and session management.
**dimensions:** {"agent_topology": "subagent_spawns", "verification_mode": "unit_tests", "session_shape": "single_shot", "repo_state": "partial_scaffold", "tool_profile": "shell_heavy", "user_persona": "staff_eng", "complexity": "medium", "value": "low", "language_runtime": "javascript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "security_privacy", "ui_surface": "api_only", "persistence": "sqlite", "testing_depth": "unit_light", "novelty_hook": "export/import round-trip as acceptance", "delivery": "static_build_preview", "modality": "text_code"}
**Depth (medium):** solid MVP — core features + light tests/smoke, avoid gold-plating. **UI fidelity:** MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required. **Effort cue:** deeper than low; still ship demoable without endless polish. FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# 2faLoginPlayground — 2FA login playground

## Complexity & fidelity lock (datagen)
- Complexity band: **medium**
- UI fidelity: MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required
- Effort cue: deeper than low; still ship demoable without endless polish
- Anti-stub: FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Product identity
Build **2faLoginPlayground** for category `security_privacy`. Seed intent (honor this product, do not genericize away):

> Create an auth playground with password login, TOTP 2FA enrollment, backup codes, and session management.

Artifact type: `web_fullstack`. Novelty hook: export/import round-trip as acceptance. Delivery: `static_build_preview`.

## 2. Target users & jobs
- Primary user implied by the seed / domain.
- Job: complete the core workflow end-to-end offline (no cloud accounts required unless seed demands otherwise).

## 3. Core entities
Define 3–8 concrete entities with fields consistent with persistence=`sqlite`.
Include at least one audit/history or list view so the UI/API is demonstrable.

## 4. Major feature areas
Implement the features implied by the seed. Depth band rules for **medium**:
- Core entities + main workflows from the seed
- Light tests or smoke as locked by testing_depth
- Clean readable UI; charts only if ui_surface implies them

Also include:
- Input validation with clear errors
- A deterministic demo/seed path OR fixture data so the app is usable with zero manual setup
- Structured logging or request log if novelty/observability hooks apply

## 5. Domain workflows
Document happy path + edge cases (empty input, invalid file/type, duplicate, not-found).
Never crash on partial input.

## 6. Data & persistence
Use persistence=`sqlite` exactly. State schema auto-created on startup when applicable.
Restart behavior documented in README.

## 7. UX / API surface
ui_surface=`api_only`:
- If `api_only` / `cli_tui`: ship CLI or HTTP API + README curls; skip rich GUI.
- If `static_html` / `desktop_window`: server-rendered or simple static pages; minimal CSS (medium fidelity).
- If `html_canvas` / `dashboard_charts`: include at least one hand-drawn chart/canvas or SVG viz.
- If `react_spa` / `mobile_web`: Vite/React (or equivalent) SPA with clear routes; keep deps lean.
Expose health/liveness (`/health` or CLI `--help` smoke).

## 8. Quality, security, reliability
Offline-first where possible. No secrets. Validate sizes/types. Deterministic demo data preferred.

## 9. Documentation & testing
README: one-command run, limitations, how to demo.
testing_depth=`unit_light` — implement that level only (do not under-ship hard; do not overbuild low).

## 10. Constraints & non-goals
Do not ignore language/ui/persistence locks. No placeholder lorem-only UI. No TODO stubs on shipped paths.

## 11. Acceptance criteria
- [ ] App boots via documented command
- [ ] Happy path from seed works with fixtures/demo
- [ ] Invalid inputs rejected clearly
- [ ] Persistence/restart behavior matches lock
- [ ] Tests/smoke required by `unit_light` pass
- [ ] README enables first run without reading source
- [ ] Visual/UI fidelity matches **medium** band

## 12. Uniqueness / anti-clone
Keep domain language from the seed. Forbidden: generic todo-app shell, Hello World, unlabeled stubs.

When done, print `DONE task_3: 2FA login playground` and start the next task immediately.

---

## Task 04 — PII redaction CLI
**workdir:** `task_security_privacy_04`
**id:** `security_privacy_04_pii-redaction-cli`
**seed (original):** Implement a PII redaction CLI that scans text/CSV for emails/phones/SSNs and writes redacted copies with a report.
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "browser_heavy", "user_persona": "pm_non_technical", "complexity": "hard", "value": "hard", "language_runtime": "csharp", "artifact_type": "cli_tool", "task_family": "security_audit", "business_domain": "legal_compliance", "ui_surface": "excel_workbook", "persistence": "json_file", "testing_depth": "unit_plus_smoke", "novelty_hook": "observability: structured logs + simple metrics endpoint", "delivery": "worker_plus_api", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# PiiRedactionCli — PII redaction CLI

## Complexity & fidelity lock (datagen)
- Complexity band: **hard**
- UI fidelity: HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable
- Effort cue: deepest; more entities, edges, and verification — still no wall-clock stop
- Anti-stub: FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Product identity
Build **PiiRedactionCli** for category `security_privacy`. Seed intent (honor this product, do not genericize away):

> Implement a PII redaction CLI that scans text/CSV for emails/phones/SSNs and writes redacted copies with a report.

Artifact type: `cli_tool`. Novelty hook: observability: structured logs + simple metrics endpoint. Delivery: `worker_plus_api`.

## 2. Target users & jobs
- Primary user implied by the seed / domain.
- Job: complete the core workflow end-to-end offline (no cloud accounts required unless seed demands otherwise).

## 3. Core entities
Define 3–8 concrete entities with fields consistent with persistence=`json_file`.
Include at least one audit/history or list view so the UI/API is demonstrable.

## 4. Major feature areas
Implement the features implied by the seed. Depth band rules for **hard**:
- Richer entity model, edge cases, and verification from acceptance list
- Multi-view or multi-endpoint surface matching ui_surface
- Stronger README + smoke/unit coverage as locked
- Higher visual fidelity when UI is not api_only/cli_tui

Also include:
- Input validation with clear errors
- A deterministic demo/seed path OR fixture data so the app is usable with zero manual setup
- Structured logging or request log if novelty/observability hooks apply

## 5. Domain workflows
Document happy path + edge cases (empty input, invalid file/type, duplicate, not-found).
Never crash on partial input.

## 6. Data & persistence
Use persistence=`json_file` exactly. State schema auto-created on startup when applicable.
Restart behavior documented in README.

## 7. UX / API surface
ui_surface=`excel_workbook`:
- If `api_only` / `cli_tui`: ship CLI or HTTP API + README curls; skip rich GUI.
- If `static_html` / `desktop_window`: server-rendered or simple static pages; minimal CSS (hard fidelity).
- If `html_canvas` / `dashboard_charts`: include at least one hand-drawn chart/canvas or SVG viz.
- If `react_spa` / `mobile_web`: Vite/React (or equivalent) SPA with clear routes; keep deps lean.
Expose health/liveness (`/health` or CLI `--help` smoke).

## 8. Quality, security, reliability
Offline-first where possible. No secrets. Validate sizes/types. Deterministic demo data preferred.

## 9. Documentation & testing
README: one-command run, limitations, how to demo.
testing_depth=`unit_plus_smoke` — implement that level only (do not under-ship hard; do not overbuild low).

## 10. Constraints & non-goals
Do not ignore language/ui/persistence locks. No placeholder lorem-only UI. No TODO stubs on shipped paths.

## 11. Acceptance criteria
- [ ] App boots via documented command
- [ ] Happy path from seed works with fixtures/demo
- [ ] Invalid inputs rejected clearly
- [ ] Persistence/restart behavior matches lock
- [ ] Tests/smoke required by `unit_plus_smoke` pass
- [ ] README enables first run without reading source
- [ ] Visual/UI fidelity matches **hard** band

## 12. Uniqueness / anti-clone
Keep domain language from the seed. Forbidden: generic todo-app shell, Hello World, unlabeled stubs.

When done, print `DONE task_4: PII redaction CLI` and start the next task immediately.

---

## Task 05 — Permission policy tester
**workdir:** `task_security_privacy_05`
**id:** `security_privacy_05_permission-policy-tester`
**seed (original):** Build a RBAC/ABAC policy tester: define roles/permissions, evaluate access queries, and show allow/deny with reasons.
**dimensions:** {"agent_topology": "tool_swarm", "verification_mode": "browser_smoke", "session_shape": "resume_mid_task", "repo_state": "legacy_messy", "tool_profile": "mixed", "user_persona": "enterprise_buyer", "complexity": "medium", "value": "medium", "language_runtime": "cpp", "artifact_type": "cli_tool", "task_family": "security_audit", "business_domain": "security_privacy", "ui_surface": "mobile_web", "persistence": "postgres_optional", "testing_depth": "browser_smoke", "novelty_hook": "plugin/extension hook (one stub plugin)", "delivery": "monorepo_client_server", "modality": "text_code"}
**Depth (medium):** solid MVP — core features + light tests/smoke, avoid gold-plating. **UI fidelity:** MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required. **Effort cue:** deeper than low; still ship demoable without endless polish. FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# PermissionPolicyTester — Permission policy tester

## Complexity & fidelity lock (datagen)
- Complexity band: **medium**
- UI fidelity: MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required
- Effort cue: deeper than low; still ship demoable without endless polish
- Anti-stub: FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Product identity
Build **PermissionPolicyTester** for category `security_privacy`. Seed intent (honor this product, do not genericize away):

> Build a RBAC/ABAC policy tester: define roles/permissions, evaluate access queries, and show allow/deny with reasons.

Artifact type: `cli_tool`. Novelty hook: plugin/extension hook (one stub plugin). Delivery: `monorepo_client_server`.

## 2. Target users & jobs
- Primary user implied by the seed / domain.
- Job: complete the core workflow end-to-end offline (no cloud accounts required unless seed demands otherwise).

## 3. Core entities
Define 3–8 concrete entities with fields consistent with persistence=`postgres_optional`.
Include at least one audit/history or list view so the UI/API is demonstrable.

## 4. Major feature areas
Implement the features implied by the seed. Depth band rules for **medium**:
- Core entities + main workflows from the seed
- Light tests or smoke as locked by testing_depth
- Clean readable UI; charts only if ui_surface implies them

Also include:
- Input validation with clear errors
- A deterministic demo/seed path OR fixture data so the app is usable with zero manual setup
- Structured logging or request log if novelty/observability hooks apply

## 5. Domain workflows
Document happy path + edge cases (empty input, invalid file/type, duplicate, not-found).
Never crash on partial input.

## 6. Data & persistence
Use persistence=`postgres_optional` exactly. State schema auto-created on startup when applicable.
Restart behavior documented in README.

## 7. UX / API surface
ui_surface=`mobile_web`:
- If `api_only` / `cli_tui`: ship CLI or HTTP API + README curls; skip rich GUI.
- If `static_html` / `desktop_window`: server-rendered or simple static pages; minimal CSS (medium fidelity).
- If `html_canvas` / `dashboard_charts`: include at least one hand-drawn chart/canvas or SVG viz.
- If `react_spa` / `mobile_web`: Vite/React (or equivalent) SPA with clear routes; keep deps lean.
Expose health/liveness (`/health` or CLI `--help` smoke).

## 8. Quality, security, reliability
Offline-first where possible. No secrets. Validate sizes/types. Deterministic demo data preferred.

## 9. Documentation & testing
README: one-command run, limitations, how to demo.
testing_depth=`browser_smoke` — implement that level only (do not under-ship hard; do not overbuild low).

## 10. Constraints & non-goals
Do not ignore language/ui/persistence locks. No placeholder lorem-only UI. No TODO stubs on shipped paths.

## 11. Acceptance criteria
- [ ] App boots via documented command
- [ ] Happy path from seed works with fixtures/demo
- [ ] Invalid inputs rejected clearly
- [ ] Persistence/restart behavior matches lock
- [ ] Tests/smoke required by `browser_smoke` pass
- [ ] README enables first run without reading source
- [ ] Visual/UI fidelity matches **medium** band

## 12. Uniqueness / anti-clone
Keep domain language from the seed. Forbidden: generic todo-app shell, Hello World, unlabeled stubs.

When done, print `DONE task_5: Permission policy tester` and start the next task immediately.

---

## Task 06 — JWT key rotation lab
**workdir:** `task_security_privacy_06`
**id:** `security_privacy_06_jwt-key-rotation-lab`
**seed (original):** Create a JWT auth service demo with key rotation, JWKS endpoint, and middleware verification tests.
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "static_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "rust", "artifact_type": "backend_api", "task_family": "coding_implement", "business_domain": "security_privacy", "ui_surface": "static_html", "persistence": "memory_only", "testing_depth": "smoke_only", "novelty_hook": "multi-theme or multi-difficulty presets", "delivery": "library_plus_demo_app", "modality": "text_code"}
**Depth (low):** thin MVP — few files, minimal polish, but every primary action must work end-to-end. **UI fidelity:** LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form. **Effort cue:** typically thinner than medium/hard (fewer files & screens), but never stop early. FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# JwtKeyRotation — JWT key rotation lab

## Complexity & fidelity lock (datagen)
- Complexity band: **low**
- UI fidelity: LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form
- Effort cue: typically thinner than medium/hard (fewer files & screens), but never stop early
- Anti-stub: FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Product identity
Build **JwtKeyRotation** for category `security_privacy`. Seed intent (honor this product, do not genericize away):

> Create a JWT auth service demo with key rotation, JWKS endpoint, and middleware verification tests.

Artifact type: `backend_api`. Novelty hook: multi-theme or multi-difficulty presets. Delivery: `library_plus_demo_app`.

## 2. Target users & jobs
- Primary user implied by the seed / domain.
- Job: complete the core workflow end-to-end offline (no cloud accounts required unless seed demands otherwise).

## 3. Core entities
Define 3–8 concrete entities with fields consistent with persistence=`memory_only`.
Include at least one audit/history or list view so the UI/API is demonstrable.

## 4. Major feature areas
Implement the features implied by the seed. Depth band rules for **low**:
- Thin file count; prefer stdlib / minimal deps
- One primary happy path + 2–3 edge cases
- Visuals: plain CSS, no animation libraries, no heavy chart frameworks

Also include:
- Input validation with clear errors
- A deterministic demo/seed path OR fixture data so the app is usable with zero manual setup
- Structured logging or request log if novelty/observability hooks apply

## 5. Domain workflows
Document happy path + edge cases (empty input, invalid file/type, duplicate, not-found).
Never crash on partial input.

## 6. Data & persistence
Use persistence=`memory_only` exactly. State schema auto-created on startup when applicable.
Restart behavior documented in README.

## 7. UX / API surface
ui_surface=`static_html`:
- If `api_only` / `cli_tui`: ship CLI or HTTP API + README curls; skip rich GUI.
- If `static_html` / `desktop_window`: server-rendered or simple static pages; minimal CSS (low fidelity).
- If `html_canvas` / `dashboard_charts`: include at least one hand-drawn chart/canvas or SVG viz.
- If `react_spa` / `mobile_web`: Vite/React (or equivalent) SPA with clear routes; keep deps lean.
Expose health/liveness (`/health` or CLI `--help` smoke).

## 8. Quality, security, reliability
Offline-first where possible. No secrets. Validate sizes/types. Deterministic demo data preferred.

## 9. Documentation & testing
README: one-command run, limitations, how to demo.
testing_depth=`smoke_only` — implement that level only (do not under-ship hard; do not overbuild low).

## 10. Constraints & non-goals
Do not ignore language/ui/persistence locks. No placeholder lorem-only UI. No TODO stubs on shipped paths.

## 11. Acceptance criteria
- [ ] App boots via documented command
- [ ] Happy path from seed works with fixtures/demo
- [ ] Invalid inputs rejected clearly
- [ ] Persistence/restart behavior matches lock
- [ ] Tests/smoke required by `smoke_only` pass
- [ ] README enables first run without reading source
- [ ] Visual/UI fidelity matches **low** band

## 12. Uniqueness / anti-clone
Keep domain language from the seed. Forbidden: generic todo-app shell, Hello World, unlabeled stubs.

When done, print `DONE task_6: JWT key rotation lab` and start the next task immediately.

---

## Task 07 — Secure file shredder utility
**workdir:** `task_security_privacy_07`
**id:** `security_privacy_07_secure-file-shredder-utility`
**seed (original):** Build a secure delete utility that overwrites files before unlink and logs operations (cross-platform best-effort).
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "approval_gated", "repo_state": "partial_scaffold", "tool_profile": "mixed", "user_persona": "staff_eng", "complexity": "hard", "value": "hard", "language_runtime": "go", "artifact_type": "cli_tool", "task_family": "coding_implement", "business_domain": "security_privacy", "ui_surface": "game_loop_window", "persistence": "sqlite", "testing_depth": "unit_plus_smoke", "novelty_hook": "chaos toggle: inject one recoverable failure path", "delivery": "one_command_dev_server", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# SecureFileShredder — Secure file shredder utility

## Complexity & fidelity lock (datagen)
- Complexity band: **hard**
- UI fidelity: HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable
- Effort cue: deepest; more entities, edges, and verification — still no wall-clock stop
- Anti-stub: FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Product identity
Build **SecureFileShredder** for category `security_privacy`. Seed intent (honor this product, do not genericize away):

> Build a secure delete utility that overwrites files before unlink and logs operations (cross-platform best-effort).

Artifact type: `cli_tool`. Novelty hook: chaos toggle: inject one recoverable failure path. Delivery: `one_command_dev_server`.

## 2. Target users & jobs
- Primary user implied by the seed / domain.
- Job: complete the core workflow end-to-end offline (no cloud accounts required unless seed demands otherwise).

## 3. Core entities
Define 3–8 concrete entities with fields consistent with persistence=`sqlite`.
Include at least one audit/history or list view so the UI/API is demonstrable.

## 4. Major feature areas
Implement the features implied by the seed. Depth band rules for **hard**:
- Richer entity model, edge cases, and verification from acceptance list
- Multi-view or multi-endpoint surface matching ui_surface
- Stronger README + smoke/unit coverage as locked
- Higher visual fidelity when UI is not api_only/cli_tui

Also include:
- Input validation with clear errors
- A deterministic demo/seed path OR fixture data so the app is usable with zero manual setup
- Structured logging or request log if novelty/observability hooks apply

## 5. Domain workflows
Document happy path + edge cases (empty input, invalid file/type, duplicate, not-found).
Never crash on partial input.

## 6. Data & persistence
Use persistence=`sqlite` exactly. State schema auto-created on startup when applicable.
Restart behavior documented in README.

## 7. UX / API surface
ui_surface=`game_loop_window`:
- If `api_only` / `cli_tui`: ship CLI or HTTP API + README curls; skip rich GUI.
- If `static_html` / `desktop_window`: server-rendered or simple static pages; minimal CSS (hard fidelity).
- If `html_canvas` / `dashboard_charts`: include at least one hand-drawn chart/canvas or SVG viz.
- If `react_spa` / `mobile_web`: Vite/React (or equivalent) SPA with clear routes; keep deps lean.
Expose health/liveness (`/health` or CLI `--help` smoke).

## 8. Quality, security, reliability
Offline-first where possible. No secrets. Validate sizes/types. Deterministic demo data preferred.

## 9. Documentation & testing
README: one-command run, limitations, how to demo.
testing_depth=`unit_plus_smoke` — implement that level only (do not under-ship hard; do not overbuild low).

## 10. Constraints & non-goals
Do not ignore language/ui/persistence locks. No placeholder lorem-only UI. No TODO stubs on shipped paths.

## 11. Acceptance criteria
- [ ] App boots via documented command
- [ ] Happy path from seed works with fixtures/demo
- [ ] Invalid inputs rejected clearly
- [ ] Persistence/restart behavior matches lock
- [ ] Tests/smoke required by `unit_plus_smoke` pass
- [ ] README enables first run without reading source
- [ ] Visual/UI fidelity matches **hard** band

## 12. Uniqueness / anti-clone
Keep domain language from the seed. Forbidden: generic todo-app shell, Hello World, unlabeled stubs.

When done, print `DONE task_7: Secure file shredder utility` and start the next task immediately.

---

## Task 08 — Consent and cookie preference center
**workdir:** `task_security_privacy_08`
**id:** `security_privacy_08_consent-and-cookie-preference-center`
**seed (original):** Create a consent preference center UI + API: categories of tracking, versioned policies, and user consent records.
**dimensions:** {"agent_topology": "single_agent", "verification_mode": "static_pass", "session_shape": "single_shot", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "low", "language_runtime": "java", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "legal_compliance", "ui_surface": "cli_tui", "persistence": "json_file", "testing_depth": "smoke_only", "novelty_hook": "domain twist: niche audience + unusual constraint", "delivery": "single_readme_run", "modality": "text_code"}
**Depth (low):** thin MVP — few files, minimal polish, but every primary action must work end-to-end. **UI fidelity:** LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form. **Effort cue:** typically thinner than medium/hard (fewer files & screens), but never stop early. FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# ConsentAndCookie — Consent and cookie preference center

## Complexity & fidelity lock (datagen)
- Complexity band: **low**
- UI fidelity: LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form
- Effort cue: typically thinner than medium/hard (fewer files & screens), but never stop early
- Anti-stub: FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Product identity
Build **ConsentAndCookie** for category `security_privacy`. Seed intent (honor this product, do not genericize away):

> Create a consent preference center UI + API: categories of tracking, versioned policies, and user consent records.

Artifact type: `web_fullstack`. Novelty hook: domain twist: niche audience + unusual constraint. Delivery: `single_readme_run`.

## 2. Target users & jobs
- Primary user implied by the seed / domain.
- Job: complete the core workflow end-to-end offline (no cloud accounts required unless seed demands otherwise).

## 3. Core entities
Define 3–8 concrete entities with fields consistent with persistence=`json_file`.
Include at least one audit/history or list view so the UI/API is demonstrable.

## 4. Major feature areas
Implement the features implied by the seed. Depth band rules for **low**:
- Thin file count; prefer stdlib / minimal deps
- One primary happy path + 2–3 edge cases
- Visuals: plain CSS, no animation libraries, no heavy chart frameworks

Also include:
- Input validation with clear errors
- A deterministic demo/seed path OR fixture data so the app is usable with zero manual setup
- Structured logging or request log if novelty/observability hooks apply

## 5. Domain workflows
Document happy path + edge cases (empty input, invalid file/type, duplicate, not-found).
Never crash on partial input.

## 6. Data & persistence
Use persistence=`json_file` exactly. State schema auto-created on startup when applicable.
Restart behavior documented in README.

## 7. UX / API surface
ui_surface=`cli_tui`:
- If `api_only` / `cli_tui`: ship CLI or HTTP API + README curls; skip rich GUI.
- If `static_html` / `desktop_window`: server-rendered or simple static pages; minimal CSS (low fidelity).
- If `html_canvas` / `dashboard_charts`: include at least one hand-drawn chart/canvas or SVG viz.
- If `react_spa` / `mobile_web`: Vite/React (or equivalent) SPA with clear routes; keep deps lean.
Expose health/liveness (`/health` or CLI `--help` smoke).

## 8. Quality, security, reliability
Offline-first where possible. No secrets. Validate sizes/types. Deterministic demo data preferred.

## 9. Documentation & testing
README: one-command run, limitations, how to demo.
testing_depth=`smoke_only` — implement that level only (do not under-ship hard; do not overbuild low).

## 10. Constraints & non-goals
Do not ignore language/ui/persistence locks. No placeholder lorem-only UI. No TODO stubs on shipped paths.

## 11. Acceptance criteria
- [ ] App boots via documented command
- [ ] Happy path from seed works with fixtures/demo
- [ ] Invalid inputs rejected clearly
- [ ] Persistence/restart behavior matches lock
- [ ] Tests/smoke required by `smoke_only` pass
- [ ] README enables first run without reading source
- [ ] Visual/UI fidelity matches **low** band

## 12. Uniqueness / anti-clone
Keep domain language from the seed. Forbidden: generic todo-app shell, Hello World, unlabeled stubs.

When done, print `DONE task_8: Consent and cookie preference center` and start the next task immediately.

---

## Task 09 — API abuse rate-limit gateway
**workdir:** `task_security_privacy_09`
**id:** `security_privacy_09_api-abuse-rate-limit-gateway`
**seed (original):** Build a rate-limit gateway middleware/service with token buckets per API key, 429 responses, and metrics.
**dimensions:** {"agent_topology": "subagent_spawns", "verification_mode": "unit_tests", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "shell_heavy", "user_persona": "staff_eng", "complexity": "medium", "value": "medium", "language_runtime": "typescript", "artifact_type": "backend_api", "task_family": "coding_implement", "business_domain": "devops_platform", "ui_surface": "html_canvas", "persistence": "sqlite", "testing_depth": "unit_light", "novelty_hook": "must include a live demo mode with sample data", "delivery": "docker_compose_optional", "modality": "text_code"}
**Depth (medium):** solid MVP — core features + light tests/smoke, avoid gold-plating. **UI fidelity:** MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required. **Effort cue:** deeper than low; still ship demoable without endless polish. FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# ApiAbuseRate — API abuse rate-limit gateway

## Complexity & fidelity lock (datagen)
- Complexity band: **medium**
- UI fidelity: MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required
- Effort cue: deeper than low; still ship demoable without endless polish
- Anti-stub: FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Product identity
Build **ApiAbuseRate** for category `security_privacy`. Seed intent (honor this product, do not genericize away):

> Build a rate-limit gateway middleware/service with token buckets per API key, 429 responses, and metrics.

Artifact type: `backend_api`. Novelty hook: must include a live demo mode with sample data. Delivery: `docker_compose_optional`.

## 2. Target users & jobs
- Primary user implied by the seed / domain.
- Job: complete the core workflow end-to-end offline (no cloud accounts required unless seed demands otherwise).

## 3. Core entities
Define 3–8 concrete entities with fields consistent with persistence=`sqlite`.
Include at least one audit/history or list view so the UI/API is demonstrable.

## 4. Major feature areas
Implement the features implied by the seed. Depth band rules for **medium**:
- Core entities + main workflows from the seed
- Light tests or smoke as locked by testing_depth
- Clean readable UI; charts only if ui_surface implies them

Also include:
- Input validation with clear errors
- A deterministic demo/seed path OR fixture data so the app is usable with zero manual setup
- Structured logging or request log if novelty/observability hooks apply

## 5. Domain workflows
Document happy path + edge cases (empty input, invalid file/type, duplicate, not-found).
Never crash on partial input.

## 6. Data & persistence
Use persistence=`sqlite` exactly. State schema auto-created on startup when applicable.
Restart behavior documented in README.

## 7. UX / API surface
ui_surface=`html_canvas`:
- If `api_only` / `cli_tui`: ship CLI or HTTP API + README curls; skip rich GUI.
- If `static_html` / `desktop_window`: server-rendered or simple static pages; minimal CSS (medium fidelity).
- If `html_canvas` / `dashboard_charts`: include at least one hand-drawn chart/canvas or SVG viz.
- If `react_spa` / `mobile_web`: Vite/React (or equivalent) SPA with clear routes; keep deps lean.
Expose health/liveness (`/health` or CLI `--help` smoke).

## 8. Quality, security, reliability
Offline-first where possible. No secrets. Validate sizes/types. Deterministic demo data preferred.

## 9. Documentation & testing
README: one-command run, limitations, how to demo.
testing_depth=`unit_light` — implement that level only (do not under-ship hard; do not overbuild low).

## 10. Constraints & non-goals
Do not ignore language/ui/persistence locks. No placeholder lorem-only UI. No TODO stubs on shipped paths.

## 11. Acceptance criteria
- [ ] App boots via documented command
- [ ] Happy path from seed works with fixtures/demo
- [ ] Invalid inputs rejected clearly
- [ ] Persistence/restart behavior matches lock
- [ ] Tests/smoke required by `unit_light` pass
- [ ] README enables first run without reading source
- [ ] Visual/UI fidelity matches **medium** band

## 12. Uniqueness / anti-clone
Keep domain language from the seed. Forbidden: generic todo-app shell, Hello World, unlabeled stubs.

When done, print `DONE task_9: API abuse rate-limit gateway` and start the next task immediately.

---

## Task 10 — Certificate expiry monitor
**workdir:** `task_security_privacy_10`
**id:** `security_privacy_10_certificate-expiry-monitor`
**seed (original):** Create a TLS certificate expiry monitor: check hosts, store notAfter dates, alert when within N days, simple dashboard.
**dimensions:** {"agent_topology": "plan_then_execute", "verification_mode": "runtime_pass", "session_shape": "resume_mid_task", "repo_state": "partial_scaffold", "tool_profile": "browser_heavy", "user_persona": "pm_non_technical", "complexity": "hard", "value": "hard", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "security_privacy", "ui_surface": "react_spa", "persistence": "memory_only", "testing_depth": "unit_plus_smoke", "novelty_hook": "offline-first; no cloud accounts", "delivery": "one_command_dev_server", "modality": "text_code"}
**Depth (hard):** full PRD depth — richer acceptance criteria and verification. **UI fidelity:** HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable. **Effort cue:** deepest; more entities, edges, and verification — still no wall-clock stop. FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths **No wall-clock or turn limit** — keep calling tools until demoable, then continue. Honor the dimensions JSON (language/UI/persistence/verification) exactly.

### Platform prompt (implement this)

# CertificateExpiryMonitor — Certificate expiry monitor

## Complexity & fidelity lock (datagen)
- Complexity band: **hard**
- UI fidelity: HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable
- Effort cue: deepest; more entities, edges, and verification — still no wall-clock stop
- Anti-stub: FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Product identity
Build **CertificateExpiryMonitor** for category `security_privacy`. Seed intent (honor this product, do not genericize away):

> Create a TLS certificate expiry monitor: check hosts, store notAfter dates, alert when within N days, simple dashboard.

Artifact type: `web_fullstack`. Novelty hook: offline-first; no cloud accounts. Delivery: `one_command_dev_server`.

## 2. Target users & jobs
- Primary user implied by the seed / domain.
- Job: complete the core workflow end-to-end offline (no cloud accounts required unless seed demands otherwise).

## 3. Core entities
Define 3–8 concrete entities with fields consistent with persistence=`memory_only`.
Include at least one audit/history or list view so the UI/API is demonstrable.

## 4. Major feature areas
Implement the features implied by the seed. Depth band rules for **hard**:
- Richer entity model, edge cases, and verification from acceptance list
- Multi-view or multi-endpoint surface matching ui_surface
- Stronger README + smoke/unit coverage as locked
- Higher visual fidelity when UI is not api_only/cli_tui

Also include:
- Input validation with clear errors
- A deterministic demo/seed path OR fixture data so the app is usable with zero manual setup
- Structured logging or request log if novelty/observability hooks apply

## 5. Domain workflows
Document happy path + edge cases (empty input, invalid file/type, duplicate, not-found).
Never crash on partial input.

## 6. Data & persistence
Use persistence=`memory_only` exactly. State schema auto-created on startup when applicable.
Restart behavior documented in README.

## 7. UX / API surface
ui_surface=`react_spa`:
- If `api_only` / `cli_tui`: ship CLI or HTTP API + README curls; skip rich GUI.
- If `static_html` / `desktop_window`: server-rendered or simple static pages; minimal CSS (hard fidelity).
- If `html_canvas` / `dashboard_charts`: include at least one hand-drawn chart/canvas or SVG viz.
- If `react_spa` / `mobile_web`: Vite/React (or equivalent) SPA with clear routes; keep deps lean.
Expose health/liveness (`/health` or CLI `--help` smoke).

## 8. Quality, security, reliability
Offline-first where possible. No secrets. Validate sizes/types. Deterministic demo data preferred.

## 9. Documentation & testing
README: one-command run, limitations, how to demo.
testing_depth=`unit_plus_smoke` — implement that level only (do not under-ship hard; do not overbuild low).

## 10. Constraints & non-goals
Do not ignore language/ui/persistence locks. No placeholder lorem-only UI. No TODO stubs on shipped paths.

## 11. Acceptance criteria
- [ ] App boots via documented command
- [ ] Happy path from seed works with fixtures/demo
- [ ] Invalid inputs rejected clearly
- [ ] Persistence/restart behavior matches lock
- [ ] Tests/smoke required by `unit_plus_smoke` pass
- [ ] README enables first run without reading source
- [ ] Visual/UI fidelity matches **hard** band

## 12. Uniqueness / anti-clone
Keep domain language from the seed. Forbidden: generic todo-app shell, Hello World, unlabeled stubs.

When done, print `DONE task_10: Certificate expiry monitor` and start the next task immediately.

---
