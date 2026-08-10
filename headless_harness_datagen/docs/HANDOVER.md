# Handover Guide — Headless Harness

Single entry point for taking over this repository. Prefer this doc over older
phase plans under `docs/archive/`.

## What this repo is

Autonomous headless harness for the Chakra gRPC coding backend.

- **Production entry:** [`main.py`](../main.py)
- **Model work:** Chakra owns Plan → implement → verify → repair → re-verify in
  **one** long-lived conversation (`session_id`).
- **Python role:** start the session, auto-approve tools, keep the conversation
  alive, emit phase resume nudges when stuck, trace events, enforce repair /
  turn limits, detect `VERDICT: PASS` + `RUNTIME_CHECK: PASS`.

Design rationale: [`refactoring.md`](refactoring.md). Full prose map of the
system: [`PROJECT_GUIDE.md`](PROJECT_GUIDE.md). Historical notes:
[`development_journal.md`](development_journal.md). Contract details:
[`architecture_reference.md`](architecture_reference.md).

## How to run

```bash
# Terminal 1 — Chakra (sets CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=55 by default)
cd headless_harness_datagen
./scripts/start_chakra.sh

# Terminal 2 — pipeline
source .venv/bin/activate
python main.py "$(cat prompt.txt)" --workdir my_project --run-id my_run
```

Useful flags: `--skip-verification`, `--max-repair-iterations`, `--max-turns`.

### Key environment variables

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` | LLM provider (via `.env`) |
| `GRPC_HOST` / `GRPC_PORT` | Chakra endpoint |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | Fire Chakra autocompact at this % of context (default 55 via `start_chakra.sh`) |
| `DISABLE_AUTO_COMPACT` | Do **not** set for long pipelines |
| `HARNESS_TURN_TIMEOUT` / inactivity / progress timeouts | Session health |

Restart Chakra after changing Chakra-side env vars or `harness/chakra/src/grpc/`.

## Architecture

```text
main.py
  → build_unified_pipeline_objective()
  → ConversationRunner + SupervisorPolicy
       → Chakra session (full chat history + autocompact)
       → StatelessAutoApprover (yes/no tools; no LLM)
       → OrchestrationState / LifecycleObserver
       → resume_nudges (phase-aware continue messages)
```

| Concern | Owner |
|---------|--------|
| Plan / implement / verify / repair decisions | Chakra (subagents) |
| Tool yes/no | Python `StatelessAutoApprover` |
| When to nudge repair / re-verify | Python `resume_nudges` |
| Chat history + compaction | Chakra |
| Traces / artifacts | Python `logs/<run-id>/pipeline/` |

## Lifecycle markers

| Marker | Who emits | Meaning |
|--------|-----------|---------|
| `ENV_STATUS: READY` | general-purpose | Project env ready |
| `IMPLEMENTATION_STATUS: COMPLETE` | general-purpose | Implementation done |
| `RUNTIME_CHECK: PASS` | verification | Build/run evidence required for PASS |
| `VERDICT: PASS/FAIL/PARTIAL` | verification only | Authoritative outcome |
| `REPAIR_STATUS: COMPLETE` | general-purpose | Repair cycle done |

Python rejects `VERDICT: PASS` without `RUNTIME_CHECK: PASS` (and without tool evidence).

## Resume nudges

When a turn ends without completion, Python may send a phase nudge instead of a
generic “Continue…”:

1. Rejected PASS → re-verify with runtime requirements
2. FAIL/PARTIAL, no `repair_plan.md` → repair planning (Plan)
3. Repair plan exists → general-purpose repair
4. Repair complete → verification re-run
5. Need implement / first verify → those nudges

Full verifier reports are written to `{repo}/repair_artifacts/last_fail_report.md`;
nudges include a short excerpt + path.

## Layout

```text
main.py                 # production pipeline
controller/             # supervisor, lifecycle, nudges, traces
verification/           # unified prompt, verdict parser, artifacts
adapter/ engine/ interface/ client/   # harness stack (not Chakra source)
scripts/                # operator/infra only (see below)
tests/                  # all automated tests
docs/                   # HANDOVER, architecture_reference, refactoring, journal
docs/archive/           # historical phase plans (read-only context)
experiments/            # run workdirs (do not delete casually)
logs/                   # regenerable traces (safe to wipe locally)
harness/                # Chakra backend — do not “clean” casually
```

### `scripts/` (keep)

| File | Role |
|------|------|
| `start_chakra.sh` | Start Chakra + autocompact defaults |
| `real_backend.py` | Env / workdir / timeout helpers (`main.py` imports this) |
| `run_autonomous.py` | Generation-only CLI |
| `run_query.py` | Manual single-turn helper |
| `run_all_real_tests.py` | Test runner over `tests/` |
| `generate_proto.py` | Proto codegen |
| `verify_chakra.py` / `smoke_chakra_subagents.py` | Backend smoke |

### `tests/`

All `test_*.py` and `phase*_common.py` helpers. First smoke checks:

```bash
python tests/test_connectivity.py
python tests/test_minimal_chat.py
python tests/test_lifecycle.py
```

## Key production files (do not delete)

- `controller/conversation_runner.py`, `supervisor_policy.py`, `orchestration_state.py`
- `controller/lifecycle.py`, `resume_nudges.py`, `workflow_common.py`
- `controller/verification_workflow.py` — **message builders only** (used by nudges)
- `verification/prompts.py` (`build_unified_pipeline_objective`), `parser.py`, `report.py`
- `adapter/`, `engine/`, `interface/`, `client/` stacks

## What was cleaned in this handover

- Removed dead `GenerationWorkflowPolicy` / `generation_workflow.py`
- Removed dead `VerificationWorkflowPolicy` class (builders kept)
- Removed legacy two-stage prompt helpers (`build_generation_objective`,
  `build_verification_stage_objective`)
- Archived historical docs under `docs/archive/`
- Moved all automated tests from `scripts/` → `tests/`

## What not to delete

- Anything under `harness/` unless you are changing the Chakra backend
- `resume_nudges.py`, `lifecycle.py`, verification **builders**, `parser.py`
- `Controller` / `ControllerRunResult` (still used by runner result adapter)

## Tests to run after changes

```bash
python tests/test_lifecycle.py
python tests/test_supervisor_policy.py
python tests/test_context_budget.py
python tests/test_verification_workflow.py
python tests/test_phase7_verification.py
python tests/test_debugger_load.py
python tests/test_debugger_contracts.py
python tests/test_debugger_taxonomy.py
python tests/test_debugger_metrics.py
python tests/test_debugger_decisions.py
python tests/test_debugger_progress.py
python tests/test_debugger_phases.py
python tests/test_debugger_retries.py
python tests/test_progress_tracker.py
python tests/test_phase_budgets.py
python tests/test_recovery_nudge.py
python tests/test_phase_gate.py
python tests/test_explore_exit.py
python tests/test_workspace_confusion.py
python tests/test_execution_policy.py
python tests/test_progress_aware_runner.py
python -c "import main"
```

Offline pipeline debugger (contracts, taxonomy, metrics, progress/stalls, reports):

```bash
python -m debugger analyze logs/run_test
python -m debugger analyze logs/habit_tracker --stall-cycles 5
```

Live controller uses **workflow** stall detection (phase/milestone only), Explore
exit criteria, recovery `ExecutionPolicy` effects, workspace-confusion reset, and
per-phase turn/tool/read budgets. Default `max_recovery_attempts=3`. Phase gate
denies verification until `IMPLEMENTATION_STATUS: COMPLETE`.
See [DEBUGGER.md](DEBUGGER.md).

Broader suite (Chakra may be required for integration tests):

```bash
python scripts/run_all_real_tests.py
```

## Controller package notes

All files under `controller/` are retained. Production uses the
`ConversationRunner` stack (orchestration, lifecycle, resume nudges, tool
approver, session health, traces). `ControllerRunResult` and Phase 6 surfaces
(`prompt_builder.py`, `Controller.decide_next_action`) remain for artifact
adapters and regression tests — do not delete them without intentionally
retiring Phase 6 decide-loop coverage.

## Known follow-ups

- Phase 6 `Controller`-based tests remain useful regression; they are not the
  production path (`ConversationRunner` is). Aggressive removal of
  `prompt_builder.py` would require gutting those tests — keep for now.
- Generated dependency manifests must list **names only** (no version pins);
  enforced in `verification/prompts.py` sandbox policy.
- Tune `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` (40–60) if long runs still blow context.
- Local `logs/` can be deleted anytime; regenerate by re-running `main.py`.
