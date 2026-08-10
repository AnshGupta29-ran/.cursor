# Category template: Monitoring / Observability Platforms

Family shape for uptime, latency, and operational health views. Each forged prompt
should target a concrete monitored estate — not abstract “Service 1”.

## Product family intent

The system periodically checks targets, stores metrics/events, detects outages, and
presents dashboards for operators to understand health over time. Configuration of
targets and intervals is part of the product.

## Identity & positioning (invent uniquely)

- Operator context (SRE for indie SaaS, campus IT, home lab, clinic network)
- Target types (HTTP URLs, ICMP hosts, TCP ports, process heartbeats — pick a set)
- Alerting posture (in-app only vs webhook stub)
- One twist (SLA burn widgets, maintenance windows, dependency maps lite, on-call notes)

## Required capability areas

### Target configuration
- CRUD for monitored targets with labels/tags
- Interval and timeout settings
- Enable/disable without delete

### Collection
- Background/periodic checker
- Persist success/failure, latency, timestamps
- Outage detection rule (consecutive failures or similar) — define it

### Visualization
- Uptime percentage windows (24h/7d or configurable)
- Latency trends
- Downtime incident list with start/end

### Investigation UX
- Target detail page with recent checks
- Filter by status/tag
- Manual “check now” action preferred

### Auth & tenancy lite
- At least single-admin auth unless seed says open local lab mode (then state it)

## UX expectations

- At-a-glance health board (green/amber/red semantics explained)
- Charts readable without zoom gymnastics
- Empty state: add first target CTA

## Data & persistence

Entities: User (optional), Target, CheckResult, Incident, NotificationChannel (optional).
SQLite or equivalent is fine; retention policy documented (e.g. keep 7–30 days).

## Quality & reliability

- Tests for outage detection logic with fixture sequences
- Checker should not crash the API on single target failures
- Time handling explicit (UTC vs local)

## Documentation & deliverables

- README: add target → wait/check now → see graph
- Explain checker scheduling mechanism
- Sample targets for local demo (localhost services OK)

## Constraints & non-goals

- Not Datadog/Prometheus-at-scale
- Not full distributed tracing unless seed asks
- Avoid random walk metrics disconnected from real checks

## Acceptance criteria checklist (customize)

- [ ] Targets can be configured and polled
- [ ] Metrics persist and render in UI
- [ ] Outages create incidents per defined rule
- [ ] Uptime/latency views match stored checks
- [ ] Checker failure on one target isolates cleanly
- [ ] Detection logic tests pass
- [ ] Local demo documented

## Variation axes

HTTP vs ICMP · incident severity · maintenance windows · multi-user · webhook alerts ·
dependency grouping · SLA focus

## Anti-clone rules

Vary estate narrative, check types, and incident rules. Do not emit identical
“ping hosts + chart.js” PRDs each time.
