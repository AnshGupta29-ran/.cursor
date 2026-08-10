# PLATFORM PROMPT — Harborline Dispatch

## Complexity & fidelity lock (datagen)
- Complexity band: **medium**
- UI fidelity: MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required
- Effort cue: deeper than low; still ship demoable without endless polish
- Anti-stub: FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Project Request / Product Identity

Build **Harborline Dispatch**, an API-only message triage service for a fictional
regional ferry + bike-share co-op ("Harborline Transit"). Riders send messages
("the dock gate at Pier 4 is jammed and my card was charged twice") and the
service classifies **sentiment**, **urgency**, and **issue category** with a
deterministic, fully local **lexicon-scoring baseline** — no external model
calls, no downloads — then routes each ticket into an operations queue with an
SLA hint. Staff engineers are the operators: every classification must expose
*why* it fired (matched terms, score margins) and low-confidence results must
land in a human review lane, never auto-silenced.

Stack (locked): **Node.js 20+, JavaScript (ESM), SQLite** via `better-sqlite3`,
plain `node:test` for tests. No Python, no ORM, no cloud APIs.

## 2. Target Users & Jobs-to-Be-Done

- **Ops dispatcher**: needs incoming rider mail auto-sorted into named queues
  (`safety`, `fare-billing`, `fleet-damage`, `accessibility`, `general`) so
  safety incidents surface first.
- **Staff engineer (primary voice)**: needs deterministic, testable scoring,
  explainable decisions, and a portable export/import for environment parity.
- **QA analyst**: needs fixtures and an export → wipe → import round-trip to
  verify persistence integrity.

## 3. Core Entities

- **Ticket** — id, channel (`email|sms|kiosk`), author handle, subject, body,
  status (`open|triaged|review|resolved`), created_at.
- **Classification** — ticket_id, sentiment (`positive|neutral|negative` +
  score), urgency (`p1..p4` + score), category, confidence (margin between top
  and runner-up scores), evidence (array of matched lexicon terms with weights).
- **Queue** — name, description, SLA minutes, routing rule snapshot.
- **AuditLog** — every ingest, classification, re-route, export, and import
  event with timestamp + payload hash.

## 4. Major Feature Areas

- **Lexicon classifier** (`src/lexicon/`): JSON lexicons for sentiment terms,
  urgency amplifiers ("trapped", "bleeding", "deadline"), and category keywords
  mapped to Harborline queues. Must handle **negation** ("not urgent"),
  **intensifiers** ("very", "extremely"), and cap body length scanned.
- **Routing engine**: pure function `(scores, thresholds) → {queue, sla, review}`
  driven by a `config/routing.json` so thresholds are tunable without code edits.
  Confidence below threshold → `review` queue, preserving the suggested queue.
- **Ingestion API**: validates payload shape, rejects empty bodies, overlong
  messages (>4000 chars), and unknown channels with clear 4xx errors
  distinguished from 500 classifier failures.
- **Explainability**: every classification response includes `evidence[]` with
  term, weight, and which lexicon fired.
- **Export/Import**: `GET /export` streams a versioned JSON bundle (tickets,
  classifications, queues, audit log). `POST /import` validates schema version
  and restores state idempotently into a wiped or fresh database.
- **Stats**: `GET /stats` returns per-queue counts, urgency histogram, and
  review-lane backlog.

## 5. Domain Workflows

**Happy path**: POST a rider message → 201 with ticket id + inline
classification → ticket appears under `GET /queues/safety/tickets` because
"gate jammed, card charged twice" hits urgency amplifier + billing keyword;
routing prefers `safety` on ties (documented precedence).

**Edge cases**: empty body → 422 with field-level errors; sarcasm/negation
("not exactly thrilled the ferry left early") still scores negative;
confidence < threshold → status `review` with `suggested_queue`; importing a
bundle into an existing DB → 409 unless `?mode=replace`; classifier never
throws on emoji-only or non-Latin input (falls back to `general`, low
confidence, flagged for review).

## 6. Data & Persistence

Single SQLite file (`data/harborline.db`, path env-overridable). Migrations run
on boot from `migrations/001_init.sql`. Seed script inserts 8 realistic rider
fixtures spanning every queue. All writes wrapped in transactions; WAL mode on.

## 7. API Surface

`POST /tickets` · `GET /tickets` (filter by queue/status/urgency) ·
`GET /tickets/:id` · `POST /tickets/:id/reroute` (human override, audited) ·
`GET /queues/:name/tickets` · `GET /stats` · `GET /export` · `POST /import` ·
`GET /health`. JSON everywhere; errors shaped `{error, code, details}`.
No auth (single-operator MVP) — document this as a non-goal.

## 8. Quality, Security, Reliability

Parameterized queries only; body-size limit; deterministic scoring (same input
→ same output, unit-tested); classifier latency < 5ms/message locally; server
must never crash on malformed JSON.

## 9. Documentation & Testing

**README**: quickstart (`npm install && npm run seed && npm start`), curl
examples for every endpoint, lexicon authoring guide, limitations (English-only
lexicon, sarcasm blind spots, no learning loop). **Static build preview**:
`npm run preview` classifies seeded fixtures and writes `preview/index.html` —
a self-contained report of queue distribution, sample evidence, and stats that
opens without the server. **Tests** (`node --test`, must finish < 10s): lexicon
negation/intensifier cases, routing precedence + review-lane fallback,
validation rejections, ingest happy path over HTTP, and the export/import
round-trip.

## 10. Constraints & Non-Goals

No external ML APIs, no model downloads, no training. No UI beyond the static
preview artifact. No multi-tenant auth. No WebSockets/streaming. Keep total
dependencies ≤ 3 runtime packages.

## 11. Acceptance Criteria

- [ ] `POST /tickets` returns structured `{sentiment, urgency, category,
      confidence, evidence[]}` for a valid rider message
- [ ] Invalid payloads (empty body, bad channel) fail with clear 4xx, never 500
- [ ] Low-confidence classifications route to `review` with a suggested queue
- [ ] `GET /queues/safety/tickets` reflects routing precedence on fixture data
- [ ] **Export → wipe DB → import → `GET /stats` and ticket payloads are
      byte-identical to pre-export state** (round-trip test passes)
- [ ] `node --test` suite green; `npm run preview` emits `preview/index.html`
- [ ] README documents limitations and curl walkthrough

## 12. Uniqueness / Anti-Clone Constraints

This is **not** a generic sentiment demo: lexicons, queues, and fixtures must
use Harborline Transit vocabulary (piers, dock gates, fare cards, vessel names),
routing must encode the safety-over-billing precedence rule, and evidence
output must name the lexicon that fired. Do not ship placeholder lexicons
("good"/"bad" only) or a todo-app-shaped CRUD with an AI label.
