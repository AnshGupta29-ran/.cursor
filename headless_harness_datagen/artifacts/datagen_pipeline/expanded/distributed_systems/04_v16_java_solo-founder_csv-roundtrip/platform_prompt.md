# VARIANT v16_java_solo-founder_csv-roundtrip - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `java`
- **user_persona**: `solo_founder`
- **novelty_hook**: `csv_roundtrip`
- **ui_surface**: `dashboard_charts`
- **persistence**: `sqlite`
- **complexity**: `low`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `java`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v16_java_solo-founder_csv-roundtrip`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v16_java_solo-founder_csv-roundtrip` when demoable.

---

## BASE PRD (honor unless mutated above)

# PLATFORM PROMPT — HarvestWire

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `java`
- **ui_surface:** `react_spa`
- **persistence:** `memory_only`
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

I'm a product manager (not an engineer) at a regional food-hub co-op. Our growers shout "what's coming off the field" and our buyers (soup kitchens, grocers, school cafeterias) each want only the categories they care about — without missing anything while their laptop is closed. **HarvestWire** is a small, self-hosted, **offline-first** "harvest ticker": an **in-process pub/sub broker** where growers **publish harvest lots and alerts to topics**, and buyers hold **named durable subscriptions** that keep collecting messages while the buyer is disconnected. No cloud accounts, no external services, no database files — everything lives in broker memory and resets cleanly on restart.

- **Stack (locked):** Java 17+ backend (JDK `com.sun.net.httpserver` or a single light lib like Javalin is fine; keep deps minimal), **React SPA** console (Vite), **in-memory only** persistence.
- **One command:** `./run.sh` (or `make dev`) starts the broker API **and** serves the SPA on a stated port. Must work on a laptop with no network after `npm install`/build.

## 2. Target users & primary jobs-to-be-done

- **Grower (publisher):** post "40 crates of kale, lot #K-118" to `lots.greens` in one action.
- **Buyer (subscriber):** create a durable subscription like `kitchen-riverbend` on `lots.greens`, walk away, come back later, and pull everything missed — newest backlog visible, nothing silently lost (within buffer limits).
- **Hub operator (me):** open the console and *see* which buyers are falling behind (**backpressure**) before they call me angry.

## 3. Core requirements / entities

In-memory domain model, domain-authentic naming:

- **Topic** — name, creation time, per-topic monotonically increasing `sequence`, publish counter, unrouted-drop counter (publish with zero subscribers = dropped + counted).
- **LotMessage** — id, topic, sequence, `key` (e.g., lot code), text payload (≤ 4 KB), `publishedAt`.
- **Subscription** — unique name, topic filter (exact topic or `lots.*` prefix wildcard), **cursor** (last acked sequence per topic), overflow policy, created/last-seen timestamps. Survives subscriber disconnect **in memory** (the "durable stub": durable across client sessions, not across process restarts — documented loudly).
- **Backlog** — per-subscription bounded ring buffer (configurable capacity, default 100) with occupancy stats.
- **StatsSnapshot** — global + per-topic + per-subscription metrics (below).

## 4. Major feature areas

1. **Broker core:** topics auto-created on first publish or subscribe; fan-out copies each message into every matching subscription's backlog; per-topic sequence numbers.
2. **Durable subscriptions (stub):** named subscriptions persist in broker memory after the consumer disconnects; a new consumer attaching with the same name **resumes from the cursor**. Explicit `ack` advances the cursor; `nack` or ack-timeout (default 30 s) triggers **redelivery** (at-least-once — state this in the README).
3. **Backpressure:** per-subscription bounded backlog with selectable overflow policy: `DROP_OLDEST` (default), `DROP_NEW`, or `REJECT_PUBLISH` (publish call returns an error for that topic when any matching subscription is full). Every drop/reject is counted.
4. **Stats API:** queue depth (pending per subscription), lag (newest topic sequence − cursor), buffer occupancy %, dropped count, redelivered count, oldest-pending-message age, per-topic publish totals.
5. **React console ("Packing Shed Board"):** topic list with publish form; subscription inspector with lag gauges and overflow-policy badges; live message tail per subscription (poll every 2 s — no websockets required); stats strip (totals: published / delivered / acked / dropped).
6. **Clean shutdown:** `SIGINT`/stop endpoint flushes nothing to disk (memory-only is explicit) but logs a final stats summary.

## 5. Domain-specific workflows

**Happy path:** create subscription `kitchen-riverbend` on `lots.greens` → publish 3 lots → `POST /poll` returns 3 → `ack` all → lag = 0 everywhere.

**Edge cases to handle and document:**
- Publish to a topic with **no subscriptions** → message unrouted, counted in stats.
- Subscriber disconnects mid-batch, reconnects later with same name → resumes from cursor, no duplicates *after* ack, redelivery of un-acked.
- Backlog overflow under `DROP_OLDEST` → oldest evicted, cursor auto-advances past evicted messages, drop counter increments; SPA badge shows "lost 12 to overflow".
- Publish with `REJECT_PUBLISH` and a full subscriber → HTTP 429-style error naming the blocking subscription.
- Wildcard `lots.*` receives `lots.greens` + `lots.orchard` but not `alerts.frost`.

## 6. Data & persistence expectations

Memory only. All state in broker data structures; **no files, no SQLite, no disk writes**. README must state plainly: restart = clean slate, and "durable" means durable across *client* disconnects within one broker run. Config (buffer sizes, ack timeout, default policy) via env vars or CLI flags with sane defaults.

## 7. UX / API surface expectations

REST JSON API (document each route in README):

- `POST /topics/{topic}/publish` — body `{key, payload}` → `{sequence}` or overflow error.
- `PUT /subscriptions` — `{name, topicFilter, overflowPolicy?, capacity?}`; `GET /subscriptions`; `DELETE /subscriptions/{name}`.
- `POST /subscriptions/{name}/poll?max=N` → batch of messages with `deliveryId`.
- `POST /subscriptions/{name}/ack` / `/nack` — by `deliveryId`.
- `GET /stats` — global + per-topic + per-subscription snapshot.

SPA served at `/`; status vocabulary consistent everywhere: `pending`, `delivered-awaiting-ack`, `acked`, `dropped`.

## 8. Quality, security, and reliability expectations

At-least-once delivery per subscription; no message loss *within* declared limits (capacity, overflow policy). Thread-safe broker (concurrent publishers/pollers). Payload cap 4 KB; reject oversized with clear error. No auth (local tool) — say so. Structured log lines for publish/ack/drop/redeliver/shutdown.

## 9. Documentation & testing expectations

- **README:** one-command start, copy-paste `curl` demo (subscribe → publish → poll → ack → check stats), "close the buyer and come back" durability demo, overflow demo, delivery-guarantees section, restart-resets warning.
- **Unit tests:** fan-out, wildcard matching, cursor resume, ack/nack + redelivery, each overflow policy, sequence monotonicity.
- **Smoke test** (`./smoke.sh` or test class): boot server, run the happy-path + one overflow scenario via HTTP, assert stats numbers, exit non-zero on failure. Runtime verification: server boots and smoke passes.

## 10. Constraints & non-goals

No Kafka-isms, no clustering, no persistence to disk, no WebSockets, no auth, no cloud SDKs, no Docker requirement, no sleeping-only fake consumers.

## 11. Acceptance criteria

- [ ] `./run.sh` brings up API + SPA with no other manual steps (post-install).
- [ ] Publish fans out to ≥2 matching subscriptions independently.
- [ ] Subscriber disconnect → reconnect with same name resumes without re-acking old messages.
- [ ] Un-acked messages are redelivered after nack/timeout; acked ones never are.
- [ ] All three overflow policies behave per spec and increment drop counters.
- [ ] `/stats` lag/depth/occupancy match a scripted publish/ack sequence exactly.
- [ ] SPA shows topics, subscriptions, live tail, and lag gauges updating without manual refresh.
- [ ] Unit tests + smoke test pass; README demo reproducible by a non-engineer.

## 12. Uniqueness / anti-clone constraints

This is **HarvestWire**, a food-hub harvest ticker — not a generic task queue or chat demo. Use domain terms (lot, crate, topic like `lots.orchard`, subscription like `kitchen-riverbend`) throughout code, UI, and README. No lorem ipsum, no "Todo", no placeholder panels; seed the demo script with realistic produce lots and a frost alert.
