# Category template: Distributed Systems / Queues / Workers

Family shape for schedulers, workers, retries, and job control planes. Prompts must
specify operational semantics — not “TODO: add queue”.

## Product family intent

Clients submit jobs; a scheduler assigns work to workers; workers heartbeat; failures
retry with defined backoff; operators observe queue depth and job state through an API
(and optional minimal UI). Concurrency and crash behavior are part of the product.

## Identity & positioning (invent uniquely)

- Workload domain (image thumbnails, invoice parsing, CI tasks, email digests — simulated OK)
- Deployment shape (single binary multi-goroutine, multi-process workers, mixed)
- Durability store (SQLite/Postgres/files)
- One twist (priorities, delayed jobs, per-tenant fair scheduling, dead-letter inspect UI)

## Required capability areas

### Job API
- Submit job with payload + type + priority
- Get job status by id
- List/filter jobs
- Cancel when safe

### Scheduler
- Pull/assign algorithm summarized
- Fairness or priority rules
- Visibility timeout / lease if applicable

### Workers
- Multiple workers demonstrable
- Heartbeats + liveness detection
- Concurrency limits per worker

### Reliability
- Retries with exponential backoff + jitter policy stated
- Max attempts → dead-letter or failed terminal state
- At-least-once vs at-most-once claim — pick and document

### Observability
- Structured logs
- Basic metrics: queue depth, in-flight, success/fail counts
- Graceful shutdown (finish or requeue current)

## UX expectations

- API-first is OK; if UI exists, focus on job table + worker health
- Clear status vocabulary
- Demo script that starts workers and submits jobs

## Data & persistence

Entities: Job, JobAttempt, Worker, Lease, DeadLetter.
Schema must survive process restart for durable modes.

## Quality & reliability

- Integration test with ≥2 workers processing jobs
- Tests for retry/backoff bookkeeping
- No lost jobs on clean shutdown path (per stated semantics)

## Documentation & deliverables

- README: start scheduler/workers, submit sample job, observe completion
- Failure injection notes (kill worker mid-job)
- Semantics doc section (delivery guarantees)

## Constraints & non-goals

- Not Kafka-at-home
- Not multi-region consensus research
- Avoid sleeping-only “workers” that don’t persist state

## Acceptance criteria checklist (customize)

- [ ] Jobs can be submitted and reach a terminal state
- [ ] Multiple workers process concurrently
- [ ] Failed jobs retry per policy then terminate correctly
- [ ] Heartbeat failure is detected
- [ ] Restart retains durable jobs
- [ ] Integration tests demonstrate multi-worker processing
- [ ] README demo works

## Variation axes

Language/runtime · priority vs FIFO · DLQ tooling · HTTP vs gRPC control · payload size
limits · tenant isolation

## Anti-clone rules

Vary workload story, scheduling policy, and failure semantics. Ban identical
“Go task queue” boilerplate each run.
