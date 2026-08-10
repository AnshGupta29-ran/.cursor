# AnswerAtlas — On-Prem Semantic FAQ Search for Enterprise Service Desks

## Complexity & fidelity lock (datagen)
- Complexity band: **medium**
- UI fidelity: MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required
- Effort cue: deeper than low; still ship demoable without endless polish
- Anti-stub: FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Project Request / Product identity
**AnswerAtlas** is a Go monorepo (`/server`, `/web`, `/plugins`) delivering semantic FAQ retrieval for mid-market enterprise service desks (shared IT/HR support). All retrieval runs **locally**: a deterministic pure-Go TF-IDF + cosine scorer (with token-bigram overlap boost) sits behind a `Scorer` interface, so a real local embedding model can be swapped in later — **no model downloads, no external AI APIs during this run**. Answers are returned ranked, cited, and bucketed into governed confidence tiers. One stub ranker plugin demonstrates the extension hook. Voice: enterprise buyer — auditability, thresholds, on-prem posture, no black boxes.

## 2. Target users & jobs-to-be-done
- **Service desk operations lead (buyer):** wants defensible answer quality, per-query audit trail, and threshold policies controlling when the system auto-answers vs. escalates.
- **Knowledge curator:** maintains FAQ entries, needs duplicate detection *before* publishing.
- **Frontline employee/agent on a phone:** types a question, gets ranked cited answers in seconds.

## 3. Core requirements / entities
- `FAQEntry`: id, question, answer, category (IT / HR / Facilities), tags, status (`draft|published|archived`), source_ref (e.g. "KB-1042"), version, updated_at.
- `ThresholdProfile`: id, name, auto_answer_min, suggest_min, is_active (exactly one active).
- `QueryLog`: id, query_text, top_k results (JSON), tier, latency_ms, scorer_version, created_at.
- `FeedbackLabel`: id, query_log_id, faq_entry_id, vote (up/down), optional comment.
- `PluginRegistry`: registered ranker plugins + enabled flag.

## 4. Major feature areas
- **Retrieval engine:** tokenize/normalize → TF-IDF vectors → cosine similarity + bigram overlap bonus; top-k with float scores; fully deterministic for fixtures.
- **Confidence tiers:** `auto-answer` (score ≥ auto_answer_min), `suggestions` (≥ suggest_min), `escalate` (below — returns handoff card with category routing hint). Distinct visual treatment per tier.
- **Admin console:** full CRUD, status transitions, and a **duplicate-compare panel**: on create/edit, show top-3 most similar existing entries side-by-side (question + score) with a "publish anyway" confirm.
- **Plugin hook:** `RankerPlugin` interface (`Name()`, `Rescore(query string, results []ScoredResult) []ScoredResult`); ship one stub, `RecencyBoost`, that nudges scores by entry `updated_at`. Toggleable via API; when disabled, results equal baseline ranking exactly.
- **Feedback + review queue:** thumbs up/down per result; admin sees a queue of downvoted (entry, query) pairs.
- **Audit:** every search logged with tier and latency; browsable read-only list.

## 5. Domain workflows
**Happy path:** first run seeds ≥12 authentic IT/HR service-desk FAQs → user searches "vpn keeps dropping on wifi" → ranked cited answers with score bars, matched-term highlighting, tier badge → user leaves feedback → curator reviews downvotes, edits entry, sees duplicate warning, publishes.
**Edge cases:** empty corpus → "no published entries" state; gibberish query → escalate card (never a fake answer); query >500 chars or empty → 400 with field error; drafts/archived excluded from search; plugin disabled mid-session → next request uses baseline; duplicate submission flagged but allowed with confirm.

## 6. Data & persistence
Repository interface with two implementations: (a) default in-memory store + JSON snapshot (`data/seed_faqs.json`, loaded on boot, writes appended), (b) Postgres via `DATABASE_URL` with SQL migrations in `/server/migrations`. **Postgres is strictly optional — the app must boot and pass all tests with zero external services.**

## 7. UX / API surface
Mobile-first web client (vanilla JS served by the Go server from `/web`): `/` search page, `/admin` console. Loading spinner during search; validation errors (400) visually distinct from engine failures (500). Endpoints:
- `POST /api/search` `{query, top_k}` → `{tier, results:[{entry_id, question, snippet, score, matched_terms, source_ref}]}`
- `GET/POST/PUT/DELETE /api/admin/faqs` (bearer `ADMIN_TOKEN` env var)
- `GET/PUT /api/admin/profiles`, `GET /api/admin/review`, `GET /api/audit`
- `POST /api/feedback`
- `GET /api/plugins`, `POST /api/plugins/{name}/toggle`
Search is unauthenticated (internal tool); admin routes require the token.

## 8. Quality, security, reliability
Validate all inputs; never crash on empty/partial data; 2s handler timeout; scores clamped [0,1]; audit log is append-only; admin token never logged; deterministic scoring so CI fixtures are stable.

## 9. Documentation & testing
README: architecture, run instructions, curl examples for every endpoint, threshold-profile tuning guide, plugin-authoring snippet, and "enabling real embeddings later" notes + limitations (English-only tokenization, no synonym expansion, TF-IDF semantic limits). Tests: Go unit/handler tests for search happy path, tier assignment, validation failures, duplicate-compare, plugin on/off equivalence. `scripts/smoke.sh`: boots server, GET `/` (asserts search UI + domain copy present), POSTs a fixture search, asserts tier + ranked JSON — the browser-smoke gate.

## 10. Constraints & non-goals
No LLM calls, no vector DB, no network fetches of models/weights, no multi-tenant SaaS, no retraining. Not a chatbot — responses are retrieval with citations, never generated prose.

## 11. Acceptance criteria
- [ ] `go run ./server` boots with no external services; seeded corpus searchable
- [ ] Valid query returns ranked results with scores, matched terms, tier badge
- [ ] Empty/oversized query → clear 400; gibberish → escalate card
- [ ] Admin CRUD works with token; duplicate-compare panel appears on similar entry
- [ ] Threshold profile edit changes tier boundaries on next search
- [ ] RecencyBoost stub plugin toggles and measurably reorders vs. baseline
- [ ] Feedback lands in review queue; searches appear in audit log with latency
- [ ] Go tests + `scripts/smoke.sh` pass; README curl examples succeed

## 12. Uniqueness / anti-clone constraints
Use service-desk vocabulary throughout (confidence tier, escalation, curator, threshold profile, source_ref) — not generic "search app" copy. No todo-list UI, no lorem ipsum, no placeholder cards; seed FAQs must be realistic ("MFA prompt fatigue lockout", "expense report per-diem caps"). The plugin must genuinely rescore results, not be a no-op label. Forbidden: ChatGPT-wrapper framing, embedding downloads at runtime, or a desktop-only layout — the client must be usable on a 375px viewport.
