# Autonomous Harness Debugger

Offline analysis of `logs/<run_id>/pipeline/` artifacts. Does **not** change
Chakra or mutate experiment repos. Writes only under `pipeline/debug/`.

## Quick start

From `headless_harness_datagen/`:

```bash
python -m debugger analyze logs/run_test
# → logs/run_test/pipeline/debug/report.md
# → logs/run_test/pipeline/debug/report.json

python -m debugger analyze logs/habit_tracker --stall-cycles 5

python -m debugger compare logs/run_a logs/run_b
# stdout table + logs/run_a/pipeline/debug/compare.json

python scripts/debug_run.py analyze logs/run_test
```

Accepts `logs/<run_id>`, `logs/<run_id>/pipeline`, or `…/pipeline/working`.

`--stall-cycles` (default **5**): consecutive controller resume decisions
without meaningful progress before flagging a forward-progress stall.

## What it does

1. **Load** — reuses `controller.trace_replay` (`load_trace_bundle`, conversation replay)
2. **Contracts** — validates lifecycle invariants (table below)
3. **Analyze** — timeline, agents, tools, files, tokens, verify/repair history
4. **Progress** — meaningful state changes vs resume cycles; stall windows
5. **Phases** — each of plan/implement/verify/repair as `never_reached` | `entered` | `succeeded` | `failed`
6. **Denials** — groups repeated identical tool denials
7. **Decisions** — `controller_decision` / `resume_nudge` / non-denial approvals
8. **Taxonomy** — **causal** primary failure; terminal limits demoted to outcome
9. **Metrics / compare** — runtime, tokens, agents, tools, controller health

## Component contracts

| Component | Key invariants | Rule IDs |
|-----------|----------------|----------|
| Bootstrap / Plan | Prefer Plan spawn / `plan.md` / `plan_agent_seen` before implement complete | `plan.before_implement` |
| Implementation | `ENV_STATUS: READY` + `IMPLEMENTATION_STATUS: COMPLETE` before first accepted verify | `impl.before_verify` |
| Verification | Authoritative `VERDICT` from verification Agent; **PASS requires `RUNTIME_CHECK: PASS`** | `verify.pass_requires_runtime_check`, `verify.authoritative_source` |
| Repair | After FAIL/PARTIAL: repair planning and/or GP repair before next verify when run continues | `repair.after_fail` |
| Resume nudges | Logged nudge kinds ∈ known set; kind matches lifecycle gap | `nudge.known_kinds` |
| Session health | `termination_reason` on `run_completed` | `health.termination_reason` |
| Tool approval | Agent spawn `subagent_type` ∈ Plan / general-purpose / verification / Explore | `tools.allowed_subagent` |

Definitions live in `debugger/contracts/definitions.py`; checks in `validate.py`.

## Meaningful progress (workflow only)

Resets the no-progress / stall counter between resume cycles:

- Phase transition (`infer_phase` change)
- Milestones: `plan.md` / Plan agent, `ENV_STATUS: READY`,
  `IMPLEMENTATION_STATUS: COMPLETE`, `REPAIR_STATUS: COMPLETE`,
  authoritative verify PASS (or accepted FAIL/PARTIAL entering repair)

**Activity that does not reset stall:** unique Reads, Edits/Writes, Bash,
`agent_completed`, first Explore spawn. Those are still counted for metrics and
phase tool/read budgets.

## Failure taxonomy (causal order)

Primary is the first causal failure, not the terminal condition:

1. Provider (quota / auth / timeout)
2. Controller exploration / forward-progress stall
3. Denial loops (identical tool denied ≥ 5 times)
4. Phase never reached (stuck before implement)
5. Lifecycle / verification / implementation failures (phase entered)
6. Limits (`max_turns`, …) — **outcome**, usually secondary

| Category | Signals |
|----------|---------|
| Provider | quota, auth, timeout strings in errors |
| Controller | progress stall; denial loops; intervention stalls; bad routing |
| Implementation | phase entered but incomplete; runtime failures |
| Verification | PASS without RUNTIME_CHECK; self-assigned verdict |
| Lifecycle | phase never reached; verify before implement; missing repair |
| Limits | `max_turns`, health terminate (outcomes) |

## Live decision logging

Traces emit `controller_decision` on every resume (including neutral) and on terminate.
`ResumeNudge` carries a `reason` string. Older traces still analyze with “partial / inferred.”

## Live progress-aware controller

`ConversationRunner` uses the same **workflow** progress definition as the offline
debugger (`controller/progress_tracker.py`):

- Only phase transitions and completed milestones reset the stall counter.
- Reads/Edits/Bash/Explore churn are activity — they do **not** clear stalls.
- Soft-continues and tool denials alone do **not**.

**Explore exit:** after Explore completes with enough in-repo Reads (default 3),
or explore tool/turn budget warn, or workspace confusion — recovery forces Plan
and may deny further Explore spawns (`ExecutionPolicy`).

**Recovery effects:** recoveries apply `RecoveryEffects` (deny subagent types,
`lock_workspace`, clear out-of-repo denial groups) — not message-only.

**Workspace confusion:** repeated `../`, absolute out-of-repo, or harness-path
denials (≥ `HARNESS_WORKSPACE_CONFUSION_THRESHOLD`, default 3) → `workspace_reset`.

**Phase budgets:** turns + tool calls + Reads per phase (no wall-clock phase
timers). Exceed → recovery then `phase_budget_exceeded:<phase>`.

After `stall_cycles` (default 5) resumes without **workflow** progress — or denial loops /
phase budget pressure — the controller issues up to **`max_recovery_attempts`
(default 3)** recovery resumes (`HARNESS_MAX_RECOVERY_ATTEMPTS`), then
terminates with a causal reason. Ordered recoveries prefer implement-first
(when `IMPLEMENTATION_STATUS` is missing), then denial/cwd strategy, then
repair after rejected PASS / FAIL.

**Phase gate:** tool approval denies `Agent` with `subagent_type=verification|verify`
until lifecycle has `implementation_complete_seen`.

| Reason | Meaning |
|--------|---------|
| `no_forward_progress` | Stall after recovery |
| `stuck_in_explore` | Explore-only without Plan/GP |
| `denial_loop` | Identical denials after recovery |
| `phase_budget_exceeded:<phase>` | Phase turn budget exceeded |

Traces include `pipeline_metrics` and `controller_decision` with
`decision=recover|terminate` and `causal_summary`. Env knobs:
`HARNESS_STALL_CYCLES`, `HARNESS_MAX_RECOVERY_ATTEMPTS`,
`HARNESS_DENIAL_LOOP_THRESHOLD`.

## Non-goals

- No web UI
- No writes under `harness/`
- Debugger never mutates experiment repos
