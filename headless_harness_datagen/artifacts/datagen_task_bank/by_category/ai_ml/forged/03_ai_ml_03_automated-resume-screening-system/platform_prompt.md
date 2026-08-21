# MeritLens — Auditable Resume Screening Workbench

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
**MeritLens** is a transparent, rubric-driven resume screening tool for **apprenticeship and skilled-trades cohort hiring** (union training centers, community-college workforce boards). Unlike black-box "AI match %" tools, every MeritLens score decomposes into named, weighted criteria a compliance officer can defend. Built in **TypeScript** (Vite + Node ≥18), delivered as (a) a **CLI** (`meritlens screen …`) and (b) a **desktop window** app (minimal Electron shell over the same renderer; renderer must also run standalone in a browser for smoke testing). All state persists in **localStorage**. No external model downloads, no network calls at runtime.

## 2. Target Users & Jobs-to-be-Done
- **Program coordinator** (enterprise buyer): "Rank 60 applicants for the Industrial Maintenance Apprentice cohort against our published rubric, in under an hour, with a paper trail."
- **Compliance reviewer**: "Show *why* each candidate was bucketed, and export the decision log for audit."

## 3. Core Requirements / Entities (localStorage namespace `meritlens.v1`)
- **RoleProfile**: name, weighted skill criteria `[{skill, synonyms[], weight}]`, section weights (certifications/experience/education), thresholds `{advance, hold}`.
- **ResumeAsset**: filename, raw text, import timestamp, validation status.
- **ScreeningResult**: resumeId, profileId, totalScore (0–100), per-criterion breakdown `{criterion, matched, evidenceSpans[], points}`, confidence (coverage-derived), matched/missing skills.
- **ReviewDecision**: resumeId, bucket (`advance|hold|reject`), decidedBy, timestamp, note.
- **AuditEvent**: append-only log of imports, scores, threshold edits, decisions.

## 4. Major Feature Areas
- **Ingestion**: paste text or upload `.txt` / `.md` resumes (multi-file); CLI accepts a folder. Unsupported/corrupt/empty files rejected with explicit reason; oversized files (>200 KB) rejected.
- **Rubric engine**: pure deterministic TypeScript; case-insensitive keyword + synonym matching, section detection, weighted sum, evidence span offsets. Same input → identical output, always.
- **Interpretation UX**: per-candidate view shows score decomposition, matched vs missing skills, and **evidence highlighting** of matched spans in the resume text.
- **Review queue**: candidates auto-bucketed into Advance/Hold/Reject by profile thresholds; human confirms or overrides every row (human-in-the-loop; nothing auto-finalizes).
- **Comparison**: side-by-side candidate-vs-job-description view (JD entered per profile).
- **Thresholds**: editable per profile with two presets (`strict`, `open-cohort`); edits logged to AuditEvent.
- **Export**: decisions + audit log as JSON and CSV.

## 5. Domain Workflows
**Happy path**: create RoleProfile (seeded sample: "Industrial Maintenance Apprentice" with OSHA-30, PLC basics, hydraulics, NCCER, blueprint reading) → import 3 sample resumes (ship as fixtures) → score → triage queue entirely by keyboard → export decision report.
**Edge cases**: zero-match resume scores 0 with "no criteria matched" explanation (never crashes); duplicate filename flagged; corrupt profile JSON in localStorage → safe reset with warning; localStorage quota error surfaced.

## 6. Data & Persistence
All entities in localStorage under one versioned key; "Export workspace" / "Import workspace" round-trips full JSON. CLI is stateless: reads files, prints ranked table, optionally writes `results.json`. No server, no database.

## 7. UX / API Surface — Accessibility-First Keyboard UX (headline feature)
- Three views: **Queue**, **Candidate Detail**, **Roles & Thresholds**. Every action operable without a mouse: `j/k` or arrows move queue selection (roving tabindex), `Enter` opens detail, `a/h/r` set bucket, `e` export, `?` opens shortcut overlay (focus-trapped, `Esc` closes, focus returns to prior element).
- `aria-live="polite"` region announces score loads and decisions ("Candidate Rivera moved to Hold"); skip-link to main; visible focus ring; WCAG AA contrast; semantic landmarks.
- Render resume text via `textContent` only (XSS-safe). Desktop window: single-file Electron `main` opening the built UI; `npm run desktop`.
- CLI: `meritlens screen --profile <file> --resumes <dir> [--json]`.

## 8. Quality, Security, Reliability
Deterministic scoring unit-tested against fixtures; no runtime network; graceful empty/partial input handling; loading state during batch scoring; validation errors distinguished from scoring errors in UI.

## 9. Documentation & Testing
- **README**: install, CLI examples, sample-data walkthrough, full keyboard map, limitations (English-only keyword heuristics, synonym bias risk, not legal/defensibility advice), how a real model could replace the rubric later.
- `npm test` — integration-light: Vitest over the engine + validation paths using fixture resumes (fast, no downloads).
- `npm run smoke` — browser smoke: build, serve, assert Queue renders and the `j`/`a` keyboard triage flow works (Playwright chromium if binaries cached; otherwise jsdom DOM smoke — document which ran; must not block PASS).

## 10. Constraints & Non-Goals
TypeScript only — **do not switch to Python** (dimension lock overrides the seed's Python mention). No PDF/DOCX parsing, no external ML APIs, no auth/multi-user, no MLOps. Legacy-messy repo: leave pre-existing files untouched; build under `src/`, `cli/`, `electron/`, `fixtures/`.

## 11. Acceptance Criteria
- [ ] `npm install && npm run dev` (or `desktop`) shows seeded profile + 3 fixture resumes scored and bucketed
- [ ] Invalid file type and empty file rejected with clear messages
- [ ] Every score shows criterion-level breakdown and highlighted evidence
- [ ] Queue fully triageable by keyboard alone; decisions announced via aria-live
- [ ] Threshold edit re-buckets candidates and writes an AuditEvent
- [ ] JSON + CSV export of decisions/audit works; CLI ranks a folder and emits JSON
- [ ] `npm test` and `npm run smoke` pass; README limitations present

## 12. Uniqueness / Anti-Clone Constraints
Not a generic "upload resume → match %" clone: must use skilled-trades terminology (journeyman, OSHA-30, NCCER, apprenticeship cohort), must expose the rubric decomposition (opaque AI scores forbidden), and must treat keyboard-first accessibility as a primary feature, not an afterthought. No placeholder UI, no lorem ipsum, no todo-app patterns.

-- implement and complete all phases wihtout stopping in between , make decisions yourself and run the final platfrm in browser for me.
