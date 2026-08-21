# VARIANT v45_rust_student-hacker_feature-flag-gates - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `rust`
- **user_persona**: `student_hacker`
- **novelty_hook**: `feature_flag_gates`
- **ui_surface**: `desktop_window`
- **persistence**: `memory_only`
- **complexity**: `medium`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `rust`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v45_rust_student-hacker_feature-flag-gates`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v45_rust_student-hacker_feature-flag-gates` when demoable.

---

## BASE PRD (honor unless mutated above)

# PLATFORM PROMPT — SlipSift

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `python`
- **ui_surface:** `static_html`
- **persistence:** `memory_only`
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
Build **SlipSift**, a Python library + demo web app that extracts structured fields (merchant, date, total, currency) from receipt images and presents them in a review dashboard with spending charts. OCR is **stubbed** (no heavy ML deps): a deterministic fake-OCR layer maps uploads to a small corpus of canned receipt texts, and users may also paste raw receipt text directly. The parsing engine is rule-based (regex + heuristics) and is the real product. The pitch: "a solo dev's pocket bookkeeper — snap, parse, confirm, see where the money went."

## 2. Target users & primary jobs-to-be-done
- **Primary persona:** a solo developer / freelancer who hoards paper receipts and wants quick totals per merchant and per day without a SaaS subscription.
- Jobs: (a) turn a receipt photo into trustworthy structured data fast; (b) eyeball and fix the extraction before trusting it; (c) see simple spending patterns at a glance; (d) reuse the parser as a library in their own scripts.

## 3. Core requirements / entities (all in-memory)
- **ReceiptSubmission**: id, original filename, OCR source (`stub` | `paste`), raw text, submitted-at timestamp.
- **ExtractionResult**: merchant, date (ISO), total (float), currency, per-field confidence (0–1), preset used, list of flagged issues (e.g., `"total not found"`, `"ambiguous date"`).
- **ReviewRecord**: links submission → result, plus user-confirmed/edited fields and status (`pending` | `confirmed`).
- No database, no auth, no users table. Everything lives in module-level Python lists/dicts and resets on restart — state this clearly in the UI footer and README.

## 4. Major feature areas
- **Library core (`slipsift` package):** `extract(text: str, preset: str = "us_corner_store") -> dict` exposing merchant/date/total/currency + confidences; importable without the web app.
- **Rule engine:** merchant = first plausible non-noise line (skip lines like `***`, card tails); date regexes for `MM/DD/YYYY`, `DD.MM.YYYY`, `Mar 4 2025`, ISO; total = amount near keywords `TOTAL`, `AMOUNT DUE`, `GRAND TOTAL` (prefer last/highest); currency inferred from symbol or preset default. Confidence degrades per missing cue.
- **Extraction presets (the multi-difficulty novelty — required):** at least three shipped profiles that *measurably change parsing behavior*:
  - `us_corner_store` — USD default, MDY date preference, lenient.
  - `eu_bistro` — EUR default, DMY preference, handles comma decimals (`12,40`).
  - `strict_audit` — any currency, caps confidence at 0.4 unless an explicit TOTAL keyword AND a parseable date are found.
- **Stub OCR layer:** deterministic mapping (e.g., hash of file bytes) to one of ≥5 bundled sample receipt texts (US grocery, EU café with comma decimals, ambiguous-date fuel receipt, faded/partial receipt missing total, itemized restaurant). Clearly labeled `OCR STUB` in code and UI; README documents how to swap in `pytesseract` later.
- **Review queue UI:** pending extractions with editable fields and per-field confidence badges; confirm saves the corrected record.
- **Dashboard charts:** server-rendered (inline SVG is fine — no JS build step): spend by merchant (bar), spend by date (bar/line), extraction confidence per receipt (color-coded). Charts reflect **confirmed** receipts only.

## 5. Domain-specific workflows
- **Happy path:** open app → click a bundled sample or upload a PNG/JPG → stub OCR yields text → extraction runs under a chosen preset → review card shows fields + confidences → user fixes the date, confirms → dashboard charts update.
- **Paste mode:** textarea submission bypasses OCR entirely (also the test-friendly path).
- **Edge cases:** non-image/oversize upload → clear 400 with supported formats listed; receipt with no TOTAL → result still returned, total `null`, issue flagged, confidence low; ambiguous `03/04/2025` → resolved by preset preference, issue `"ambiguous date: assumed MDY"` recorded; empty/garbage text → all-null result with zero confidence, no crash.

## 6. Data & persistence expectations
Memory-only: a simple `store.py` (lists + dicts) is enough. Confirmed edits mutate the in-memory record. No files written except optional upload temp handling. README must state data vanishes on restart and that swapping in SQLite is a documented one-paragraph future step.

## 7. UX / API surface expectations
- Single-page-ish Flask app (or equivalent micro-framework), `render_template_string` acceptable to keep file count low. Pages/sections: submit (upload + paste + preset selector), review queue, dashboard.
- JSON API mirroring the UI:
  - `POST /api/extract` — multipart image **or** JSON `{"text": ..., "preset": ...}` → ExtractionResult JSON.
  - `GET /api/receipts` — all records with status.
  - `POST /api/receipts/<id>/confirm` — accepts corrected fields.
  - `GET /api/stats` — aggregates backing the charts.
- Loading state during "OCR" (a brief artificial delay is fine), distinct error rendering for validation failures vs parse failures.

## 8. Quality, security, and reliability expectations
Validate extension + size (≤2 MB) on upload; never trust pasted text length (cap ~10k chars); all parsing is pure-Python regex (no eval, no subprocess); parser must never raise on malformed input — return a low-confidence result with issues instead. Keep total deps to Flask + pytest (stdlib-only parsing; no PIL/torch/tesseract required to run).

## 9. Documentation & testing expectations
- **README:** product blurb, `pip install -r requirements.txt`, `python app.py`, library usage snippet (`from slipsift import extract`), curl example for `/api/extract`, preset comparison table, OCR-swap instructions, limitations (stubbed OCR, English-ish receipts, in-memory loss, rule fragility).
- **Smoke tests only:** one small test file — parser happy path on 2 canned receipts (including the comma-decimal one), one API test posting pasted text and asserting the JSON schema, one invalid-upload rejection test. All deterministic, all offline, run in <5 s.

## 10. Constraints & non-goals
No real OCR models, no image preprocessing, no line-item extraction, no multi-currency conversion, no auth, no database, no export formats beyond the JSON API. Do not add features beyond this list; polish the listed ones instead.

## 11. Acceptance criteria
- [ ] `from slipsift import extract; extract(SAMPLE, preset="eu_bistro")` returns merchant/date/total/currency + confidences.
- [ ] App runs with `python app.py`; upload, paste, review-confirm, and dashboard all work end-to-end.
- [ ] All ≥3 presets demonstrably alter at least one extraction on the bundled samples (shown in README table or test).
- [ ] Missing-total and ambiguous-date receipts surface flagged issues, not crashes.
- [ ] Charts render confirmed data and update after a confirm.
- [ ] `pytest` smoke suite passes offline in seconds.
- [ ] README limitations + OCR-stub disclosure present.

## 12. Uniqueness / anti-clone constraints
This is not a generic CRUD or todo app: no task lists, no "items", no placeholder lorem-ipsum UI. Use receipt-domain vocabulary throughout (merchant, tender, grand total, VAT line, review queue, extraction profile). Presets must be functional parsing profiles, not cosmetic renames. The dashboard must show receipt-spend charts specifically, not a generic counter widget. Ship few files, real behavior, zero dead buttons.

- finish full repo level platform and run it in my browser when it is fully implemented.
