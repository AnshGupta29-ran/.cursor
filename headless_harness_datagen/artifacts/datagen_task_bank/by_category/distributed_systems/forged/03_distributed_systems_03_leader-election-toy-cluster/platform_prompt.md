# GAVEL — Raft-Lite Failover Rehearsal Rig

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `python`
- **ui_surface:** `html_canvas`
- **persistence:** `sqlite`
- **complexity:** `medium`
- Do **not** rewrite this project in a different language.

## Complexity & fidelity lock (datagen)
- Complexity band: **medium**
- UI fidelity: MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required
- Effort cue: deeper than low; still ship demoable without endless polish
- Anti-stub: FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.
- **Build-first (anti time-waste):** Implement immediately from this PRD. Forbidden: WebSearch/WebFetch, browsing docs sites, winget/ripgrep installs for searching, Explore/research subagents, Grep/Glob fishing across sibling tasks. At most 2 targeted reads inside this task workdir before Write/Edit. Low = few files shipped fast — do not gold-plate.


## 1. Project Request / Product identity

Build **Gavel**, a single-host, multi-threaded Python 3.10+ cluster simulator that runs a raft-lite leader-election protocol and uses the elected leader to issue **epoch-fenced dispatch grants** (monotonic fencing tokens). The product is a *failover rehearsal rig* for engineers who need to demonstrate — not just claim — that a control plane survives leader loss, that terms are monotonic, and that a stale leader's grants are rejected after failover. A live HTML canvas dashboard renders the node ring, heartbeat pulses, and term history in real time. A scripted **demo mode** seeds sample data, runs the cluster, kills the leader on cue, and narrates the failover.

Voice: a staff engineer's internal tool — precise semantics, explicit guarantees, zero hand-waving.

## 2. Target users & primary jobs-to-be-done

- **Staff engineer** rehearsing a failover story before a design review: "show me the cluster elect, lose, and replace a leader in under a minute."
- **Onboarder** learning election mechanics: watch heartbeats, timeouts, and terms change live instead of reading a paper.
- **Tooling engineer** validating fencing-token reasoning: prove a partitioned ex-leader cannot issue valid grants.

## 3. Core requirements / entities

Persisted in **SQLite** (single file, e.g. `gavel.db`):

- **Node** — id, name, role (`follower|candidate|leader`), state (`alive|down`), current term, voted-for, last heartbeat timestamp, concurrency-safe in-process runtime.
- **ElectionEvent** — audit row: term, candidate, votes received, outcome (`won|split|stepped_down`), wall time.
- **HeartbeatEvent** — leader id, term, received-by set, timestamp (sampled/aggregated is fine; don't log every beat).
- **GrantTicket** — fencing token: monotonically increasing `(term, seq)` pair, issued-by node, payload label, status (`active|revoked|rejected_stale`).
- **ClusterMeta** — durable `current_term` / `voted_for` per node so restart restores election state honestly.

Runtime (in-memory OK): election timers, heartbeat scheduler, message-drop flags for simulated partition.

## 4. Major feature areas

- **Raft-lite election**: randomized election timeouts (e.g. 150–300 ms scaled), candidacy, majority vote of alive nodes, split-vote retry with backoff + jitter, step-down on observing a higher term. Log replication of arbitrary entries is **out of scope** — only term/vote/grant state exists.
- **Heartbeat & liveness**: leader broadcasts beats on an interval; followers reset timers on beat; missed beats past timeout trigger election. Dead-node detection must be observable in UI and logs.
- **Fencing-token grants**: only the current-term leader issues `GrantTicket`s with strictly increasing `(term, seq)`. Acceptance rule: a ticket is valid only if its term equals the cluster's durable current term **and** its issuer still holds leadership — a revived ex-leader's tickets are rejected as `rejected_stale`. This is the product's headline guarantee; document it as **at-most-once grant validity per term**.
- **Failure injection**: CLI/API to `kill <node>` (stops its threads, marks down), `revive <node>`, and `partition <node>` (drops inbound messages while keeping it running, so it still issues *stale* grants that must be rejected).
- **Live demo mode**: `python -m gavel demo` boots a 5-node cluster with sample data (named nodes, pre-seeded grant requests like `cron-dispatch`, `cache-warmer`, `report-render`), serves the dashboard, waits ~5s, then kills the leader, narrates re-election, revives the old leader, and shows its stale grant being rejected — all visible on the canvas.
- **Observability**: structured (JSON-line) logs for elections, heartbeats, grants, rejections; a metrics endpoint or CLI `status` showing current term, leader id, alive/dead counts, grants issued/rejected.

## 5. Domain-specific workflows

**Happy path**: start 5 nodes → election completes within ~2 timeout windows → leader heartbeats → client requests 3 grants → all issued with increasing tokens → dashboard shows green ring, pulses, term badge.

**Failover**: kill leader → followers time out → new election at term+1 → new leader resumes grants with higher term → old tickets remain historically valid but no *new* stale tickets accepted.

**Edge cases**: split vote (even cluster / simultaneous candidacy) → backoff and retry until majority; revive ex-leader → it observes higher term and steps down to follower; revive partitioned node that kept "leading" → its grant attempt rejected and logged as `rejected_stale`; full-cluster restart → terms/votes reloaded from SQLite, fresh election proceeds from persisted term (no term regression).

## 6. Data & persistence expectations

SQLite via stdlib `sqlite3`, WAL or busy-timeout to tolerate multi-threaded access. Schema must survive process kill/restart: durable per-node `(current_term, voted_for)` and the full grant ledger. Term is monotonic across restarts — a test must prove a restarted node never votes or leads with a lower term than its persisted value.

## 7. UX / API surface expectations

- **Dashboard**: one HTML page served by the control process using `<canvas>` (vanilla JS, no build step): nodes drawn as a ring; leader highlighted with crown/term badge; animated heartbeat pulses along edges; dead nodes greyed; partitioned nodes hatched; live event ticker (elections, grants, stale rejections); polls a JSON status endpoint every ~500 ms.
- **CLI** (`python -m gavel …`): `start --nodes 5`, `status`, `kill <name>`, `revive <name>`, `partition <name>`, `grant <label>`, `demo`. Human-readable output with correct vocabulary (term, candidate, majority, fencing token).
- Prefer **stdlib only** (`http.server`, `threading`, `sqlite3`, `json`, `unittest`) so the repo runs with zero pip installs.

## 8. Quality, security, and reliability expectations

- Guarantee to state in README: leadership is exclusive per term; fencing tokens are monotonic; delivery semantics for grants = at-most-once validity per term.
- Graceful shutdown: `SIGINT`/CLI stop finishes in-flight grant issuance, flushes SQLite, exits clean with no lost durable state.
- No unbounded threads; election loops must exit on node stop. No external network exposure beyond localhost.

## 9. Documentation & testing expectations

- **README**: architecture sketch (ASCII), semantics/guarantees section, quickstart (`demo` in one command), failure-injection recipes ("kill the leader mid-grant", "partition the leader and watch stale rejection"), schema notes.
- **Unit tests, light** (`unittest`, runnable via `python -m unittest`): majority-win logic, split-vote retry, term monotonicity across simulated restart, stale-grant rejection after failover, heartbeat-timeout triggers candidacy, persistence round-trip of term/vote. ~8–12 focused tests; no heavy fixtures.

## 10. Constraints & non-goals

- Not real Raft: no arbitrary log replication, no snapshots, no membership changes.
- Not multi-process/multi-machine: threads on one host; partitions are simulated message drops, not netem.
- No frameworks required; **docker-compose.yml optional** (single service wrapping `demo`) and must not be needed for the core flow.
- No sleeping-only theater: elections and fencing checks must consult persisted state.

## 11. Acceptance criteria

- [ ] 5-node cluster elects exactly one leader per term; dashboard shows it live on canvas.
- [ ] Killing the leader triggers re-election at term+1 without manual intervention.
- [ ] Grants carry monotonic `(term, seq)` tokens; a revived/partitioned ex-leader's grant is rejected and logged.
- [ ] Restart preserves terms and grant ledger; no term regression.
- [ ] `demo` mode runs the full scripted failover with sample data, unattended.
- [ ] Unit tests pass and cover election, fencing, and persistence.
- [ ] README documents guarantees and failure-injection recipes.

## 12. Uniqueness / anti-clone constraints

This is **not** a generic task queue and not a paper-summary Raft toy: the domain twist is *fencing-token grant issuance as the election's payload*, with stale-leader rejection as the demonstrable guarantee. Ban placeholder UIs, "TODO" semantics, and heartbeat loops that don't drive real elections. Use domain-authentic vocabulary (term, candidacy, majority, fencing token, step-down) throughout code, CLI, and docs.
