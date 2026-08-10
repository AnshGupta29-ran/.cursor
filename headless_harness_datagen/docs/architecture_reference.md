# Architecture Reference — Common Harness Contract

Long-term technical reference for the backend-independent harness interface (Phase 3).

## Harness Interface

The `Harness` abstract base class (`interface/harness.py`) is the only API that higher layers should use to operate a backend.

### Core operations

| Operation | Responsibility |
|---|---|
| `connect(config)` | Establish backend connection |
| `disconnect()` | Release connection resources |
| `connection_info()` | Report connection state |
| `capabilities()` | Advertise supported features |
| `create_session(request)` | Start a new session |
| `resume_session(request)` | Continue an existing session |
| `send_turn(session, request)` | Begin a streamed user turn |
| `get_session_status(session)` | Query session metadata |
| `close_session(session)` | Close session from controller side |

### Turn stream operations

`send_turn()` returns a `TurnStream` with:

| Operation | Responsibility |
|---|---|
| `__iter__()` | Yield harness events until terminal |
| `respond(response)` | Answer `intervention_required` events |
| `cancel(request)` | Interrupt active turn |
| `result()` | Read final `TurnResult` after terminal event |

## Request Models

Defined in `interface/models/requests.py`:

- `ConnectionConfig` — endpoint + generic options bag
- `CreateSessionRequest` — initial session parameters
- `ResumeSessionRequest` — resume by `session_id`
- `SendMessageRequest` — user message for a turn
- `InterventionResponse` — reply to intervention prompts
- `InterruptRequest` — cancellation reason

## Response Models

Defined in `interface/models/responses.py`:

- `ConnectionInfo` — connection status and adapter metadata
- `TurnResult` — final text, usage, identifiers
- `SessionStatus` — session state snapshot
- `SessionCloseResult` — close confirmation
- `UsageStats` — token accounting

## Event Models

Defined in `interface/events.py`:

| Event Type | Meaning |
|---|---|
| `text_delta` | Streamed assistant text fragment |
| `tool_started` | Tool invocation announced |
| `tool_completed` | Tool output available |
| `intervention_required` | Controller input needed |
| `turn_completed` | Successful turn terminal event |
| `turn_failed` | Failed turn terminal event |

Terminal events: `turn_completed`, `turn_failed`.

## Session Model

`HarnessSession` (`interface/models/session.py`):

- `session_id` — opaque identifier
- `state` — `active` or `closed`
- `working_directory` — optional execution context
- `metadata` — adapter-neutral key/value metadata
- `turn_count` — turns executed in this handle

## Capability Model

`HarnessCapability` (`interface/capabilities.py`) allows adapters to declare support for:

- connect / disconnect
- streaming
- sessions / session resume
- tool execution
- interactive approval
- cancellation
- model override
- working directory

Controllers should check `capabilities().supports(...)` before optional operations.

## Design Principles

1. **Backend independence** — no transport/protocol names in `interface/`.
2. **Capability-based** — optional features are explicit, not assumed.
3. **Event-driven turns** — streaming and interventions are first-class.
4. **Adapter translation** — all backend specifics remain in adapter layers.
5. **Stable contract** — controller and execution engine depend only on this API.

## Extension Guidelines

### Adding a new harness backend

1. Implement `Harness` and `TurnStream`.
2. Translate backend requests to harness request models.
3. Translate backend events to `HarnessEvent` union members.
4. Advertise accurate `HarnessCapabilities`.
5. Add adapter tests; do not modify controller/conversation layers.

### Adding a new optional capability

1. Add enum value to `HarnessCapability`.
2. Document semantics in this reference.
3. Extend adapter(s) that support it.
4. Update controller logic to handle absence gracefully.

### Phase 2 → contract event mapping

Reference mapping for adapters (`interface/validation/event_mapping.py`):

| Backend event (Phase 2) | Harness event |
|---|---|
| `text_chunk` | `text_delta` |
| `tool_start` | `tool_started` |
| `tool_result` | `tool_completed` |
| `action_required` | `intervention_required` |
| `done` | `turn_completed` |
| `error` | `turn_failed` |

## Package Layout

```text
interface/
├── harness.py              # Harness + TurnStream ABCs
├── capabilities.py         # Capability model
├── events.py                 # Universal event union
├── exceptions.py             # Contract errors
├── models/
│   ├── requests.py
│   ├── responses.py
│   └── session.py
├── validation/
│   └── event_mapping.py    # Adapter translation reference
└── reference/
    └── in_memory_harness.py  # Contract validation implementation
```

## Validation

Phase 3 validation scripts:

- `tests/test_phase3_interface.py`
- `tests/test_phase3_models.py`
- `tests/test_phase3_events.py`
- `tests/test_phase3_contract_validation.py`

Progress log: `docs/development_journal.md`

---

## Chakra Adapter Architecture

Production Chakra integration lives in `adapter/chakra/`. Higher layers use `ChakraHarness` (implements `Harness`) and must not import `ChakraClient` directly.

```text
Controller / Execution Engine
            │
            ▼
      Harness (ABC)
            │
            ▼
      ChakraHarness
      ┌─────┴─────┐
      ▼           ▼
 ChakraTurnStream  session/config helpers
      │
      ▼
 translator.py
      │
      ▼
  ChakraClient (client/)
      │
      ▼
  Chakra gRPC backend
```

## Request Translation

| Harness request | Chakra translation |
|---|---|
| `ConnectionConfig` | gRPC host/port + connect timeout |
| `CreateSessionRequest` | new `HarnessSession.session_id` (UUID) |
| `ResumeSessionRequest` | reuse `session_id` on `ChatRequest` |
| `SendMessageRequest` | `ChatRequest.message` + optional model |
| `InterventionResponse` | `UserInput(prompt_id, reply)` |
| `InterruptRequest` | `CancelSignal(reason)` |

## Event Translation

Implemented in `adapter/chakra/translator.py`:

| Chakra `ServerEvent` | Harness event |
|---|---|
| `text_chunk` | `TextDeltaEvent` |
| `tool_start` | `ToolStartedEvent` |
| `tool_result` | `ToolCompletedEvent` |
| `action_required` | `InterventionRequiredEvent` |
| `done` | `TurnCompletedEvent` |
| `error` | `TurnFailedEvent` |

## Session Mapping

- `HarnessSession.session_id` is sent as Chakra `ChatRequest.session_id`.
- Each harness turn opens a new Chakra bidi stream.
- `close_session()` marks session closed client-side; Chakra retains in-memory history until eviction.
- `get_session_status()` reads from the harness session handle.

## Chakra gRPC Built-in Subagents (Phase 1)

Subagent integration follows [explicit_backend_agent_call.md](explicit_backend_agent_call.md). The harness orchestrates **when** to invoke Chakra subagents; Chakra owns **how** they run.

### Registry

`harness/chakra/src/grpc/builtInGrpcAgents.ts` exports `GRPC_BUILTIN_AGENTS` — explicit imports that bypass `getBuiltInAgents()` feature flags and GrowthBook gates:

| `subagent_type` | Agent module | Typical harness use (upcoming phases) |
|---|---|---|
| `Plan` | `planAgent.ts` | Generation step 1 — implementation plan → `plan.md` |
| `general-purpose` | `generalPurposeAgent.ts` | Implementation and repair |
| `verification` | `verificationAgent.ts` | Adversarial verify; authoritative `VERDICT:` |
| `Explore` | `exploreAgent.ts` | Read-only repo search |

`harness/chakra/src/grpc/server.ts` passes `agents: GRPC_BUILTIN_AGENTS` into each `QueryEngine` instance. The main agent invokes subagents via the `Agent` tool (`subagent_type` argument). Every nested tool call still surfaces as `action_required` on gRPC; the harness controller approves or auto-approves.

### Verification

```bash
# Terminal 1 — restart after grpc changes
./scripts/start_chakra.sh
# expect: gRPC built-in subagents: Plan, general-purpose, verification, Explore

# Terminal 2
python scripts/smoke_chakra_subagents.py
```

### Roadmap (later phases)

1. **Phase 1** — register subagents on gRPC (done)
2. **Phase 2** — generation workflow: mandatory `Plan` → `general-purpose` → `plan.md` (done)
3. **Phase 3** — completion guard requires `verification` + `VERDICT: PASS` (done)
4. **Phases 4–5** — verify ↔ repair orchestration via Chakra subagents (done)
5. **Phase 6** — verification loop hardening: subagent-only VERDICT evidence (done)
6. **Phase 7** — Explore subagent hints in generation prompts (done)
7. **Phase 8** — deterministic intervention policy

## Two-stage pipeline (generation + verification)

**Superseded.** Current `main.py` uses a **single** Chakra conversation (Phase 7).
See [Repository Verification (Phase 7)](#repository-verification-phase-7) and
[`HANDOVER.md`](HANDOVER.md).

Historical note: an older design used `GenerationWorkflowPolicy` then a second
conversation with `VerificationWorkflowPolicy`. Those policy classes have been
removed; verification/repair **message builders** remain in
`controller/verification_workflow.py` for resume nudges.

Unit tests: `tests/test_verification_workflow.py`, `tests/test_lifecycle.py`

## Adapter Responsibilities

| Module | Responsibility |
|---|---|
| `harness.py` | `Harness` implementation, connection + session orchestration |
| `stream.py` | `TurnStream` over Chakra bidi chat |
| `translator.py` | Event translation |
| `session.py` | Session create/resume/status/close mapping |
| `config.py` | `ConnectionConfig` → Chakra endpoint resolution |

## Validation Results

Phase 4 scripts (all PASS against mock Chakra server):

- `tests/test_phase4_connection.py` — Step 4.1
- `tests/test_phase4_session.py` — Step 4.2
- `tests/test_phase4_turn.py` — Step 4.3
- `tests/test_phase4_translator.py` — Step 4.4
- `tests/test_phase4_adapter_validation.py` — Step 4.5

Isolation rule: `interface/` must not import `client.chakra_client`.

---

## Execution Engine

The execution engine (`engine/`) is the backend-independent execution framework that sits above the harness interface. It coordinates session lifecycle, turn execution, event processing, and conversation state — but does **not** make autonomous decisions. Decision-making is supplied by the controller (Phase 6) via `InterventionHandler` callbacks and turn messages.

```text
Controller (Phase 6)
        │
        ▼
ExecutionEngine
        │
        ├── ConversationState / TurnState
        ├── EventDispatcher
        └── EngineObserver notifications
        │
        ▼
      Harness (ABC)
        │
        ▼
      Adapter (e.g. ChakraHarness)
```

### Package layout

```text
engine/
├── execution_engine.py      # Execution loop and lifecycle API
├── state.py                 # ConversationState, TurnState, snapshots
├── dispatcher.py            # HarnessEvent → state updates
├── types.py                 # InterventionHandler, EngineObserver
└── exceptions.py            # Engine-specific errors
```

### Public API

| Component | Responsibility |
|---|---|
| `ExecutionEngine` | Start/close conversations, execute turns, reconstruct state |
| `StartConversationRequest` | Optional working directory, model, metadata |
| `EventDispatcher` | Route harness events into mutable conversation state |
| `ConversationState` | History, turns, active turn, harness session handle |
| `InterventionHandler` | External callback for `intervention_required` events |
| `EngineObserver` | Lifecycle notifications for controller integration |

## Conversation Lifecycle

| Phase | Engine method | State transition |
|---|---|---|
| Start | `start_conversation()` | `CREATED` → `ACTIVE` |
| Turn | `execute_turn()` | `ACTIVE` → `TURN_IN_PROGRESS` → `ACTIVE` |
| Intervention | (within turn) | `TURN_IN_PROGRESS` → `AWAITING_INTERVENTION` → `TURN_IN_PROGRESS` |
| Failure | terminal `turn_failed` | `TURN_IN_PROGRESS` → `FAILED` |
| Cancel | `cancel_active_turn()` | active turn → `CANCELLED`, conversation → `ACTIVE` |
| Close | `close_conversation()` | `ACTIVE` → `CLOSED` |

A conversation owns one `HarnessSession`. Each `execute_turn()` opens a new `TurnStream`, processes events until a terminal event, and records the result on the turn.

## State Management

`ConversationState` (`engine/state.py`) is the authoritative in-memory model:

| Field | Purpose |
|---|---|
| `conversation_id` | Opaque engine-level identifier |
| `harness_session` | Live session handle passed to harness operations |
| `status` | `ConversationStatus` enum |
| `history` | Ordered `HistoryEntry` list (user/assistant/system) |
| `turns` | Completed and in-progress turn records |
| `active_turn` | Current turn while streaming |
| `metadata` | Caller-supplied key/value bag |

`TurnState` tracks per-turn execution:

- `user_message`, `streamed_text`, `events` (full `EventRecord` log)
- `pending_intervention` while awaiting operator input
- `result` (`TurnResult`) after successful completion

**Reconstruction:** `ConversationState.snapshot()` and `from_snapshot()` produce a serializable view for validation and future controller context. `reconstruct(conversation_id)` exposes this on the engine.

## Event Processing Pipeline

```text
TurnStream.__iter__()
        │
        ▼
EventDispatcher.dispatch(state, event)
        │
        ├── append EventRecord to active turn
        ├── update streamed_text (text_delta)
        ├── transition status (intervention / terminal)
        └── return DispatchResult
        │
        ▼
ExecutionEngine._process_stream()
        │
        ├── if requires_intervention → InterventionHandler → stream.respond()
        ├── if terminal turn_completed → complete turn, clear active_turn
        └── if terminal turn_failed → raise ConversationStateError
```

`DispatchResult` fields:

- `is_terminal` — stop iterating the stream
- `requires_intervention` — engine must call handler and `stream.respond()`

## Execution Flow

Typical single-turn flow:

1. `engine.start_conversation()` → harness `create_session()`
2. `engine.execute_turn(id, message, intervention_handler=handler)`
3. Engine creates `TurnState`, calls harness `send_turn()`
4. For each harness event: dispatch → optional intervention → terminal check
5. On `turn_completed`: attach `stream.result()` to turn, return `TurnResult`
6. `engine.close_conversation()` → harness `close_session()`

If `intervention_handler` is omitted and the harness emits `intervention_required`, the engine raises `InterventionRequiredError` and aborts the active turn so the conversation remains usable.

## Controller Integration (Phase 5 → 6 boundary)

The execution engine exposes hooks for the controller:

| Hook | Type | When invoked |
|---|---|---|
| `InterventionHandler` | `Callable[[InterventionRequiredEvent, ConversationState], str \| InterventionResponse]` | On `intervention_required` during a turn |
| `EngineObserver` | `Callable[[EngineNotification], None]` | On lifecycle transitions and each event |

`EngineNotificationKind` values: `conversation_started`, `turn_started`, `event_received`, `intervention_required`, `intervention_resolved`, `turn_completed`, `turn_failed`, `conversation_closed`.

The controller chooses user messages and intervention responses; the execution engine enforces state consistency and harness protocol.

### Isolation rule (engine)

`engine/` must not import `client/`, `adapter/`, gRPC, or protobuf. Validation: `tests/phase5_common.py::scan_engine_isolation()`.

## Validation Results (Phase 5)

| Script | Step | Backend |
|---|---|---|
| `tests/test_phase5_state.py` | 5.1 — state model & reconstruction | Unit |
| `tests/test_phase5_dispatcher.py` | 5.2 — event dispatcher | Unit |
| `tests/test_phase5_engine.py` | 5.3 — execution engine | In-memory harness |
| `tests/test_phase5_engine_real.py` | 5.4 — full lifecycle | Real Chakra + LLM |

---

## Controller Architecture

The controller (`controller/`) is the autonomous decision-making layer. It observes execution state via the execution engine, reasons with an LLM, and produces executable actions. It never talks to backends directly.

```text
User objective
      │
      ▼
  Controller
      │  LLM reasoning (OPENAI_*)
      │  ControllerContext
      ▼
ExecutionEngine
      ▼
    Harness
      ▼
   Adapter
```

### Package layout

```text
controller/
├── controller.py        # Autonomous run loop
├── context_builder.py # ControllerContext assembly
├── prompt_builder.py  # System/user prompts
├── decision.py        # Action model and JSON parsing
├── policies.py        # DecisionPolicy with retry
├── llm.py             # OpenAI-compatible client
└── exceptions.py
```

## Prompting Strategy

| Element | Definition |
|---|---|
| Role | Autonomous orchestrator — plans and instructs the backend agent |
| Actions | `send_message`, `complete` |
| Format | Single JSON object per decision |
| Constraints | Non-empty `message` or `summary`; incremental progress; no backend protocol details |

Intervention prompts use a separate system message returning JSON `{"response": "yes"|"no", "reasoning": "..."}`.

## Context Construction

`ControllerContext` (`controller/context_builder.py`) includes:

| Field | Source |
|---|---|
| `objective` | User-provided run goal |
| `conversation_id`, `conversation_status` | `ConversationState` |
| `session_id`, `session_state`, `working_directory` | `HarnessSession` |
| `history` | Ordered user/assistant/system messages |
| `recent_events` | Event records from active or last turn |
| `last_assistant_message`, `last_user_message` | Derived from history |

`build_intervention_context()` adds intervention id, prompt, and kind during active turns.

## Decision Process

1. `build_context(state, objective)` — backend-neutral snapshot
2. `build_decision_messages(context)` — system + user prompts
3. `DecisionPolicy.decide()` — LLM call, parse JSON, validate, retry on invalid output
4. Execute `ControllerAction` via execution engine

## Action Model

| Action | Fields | Engine operation |
|---|---|---|
| `send_message` | `message`, `reasoning` | `execute_turn(conversation_id, message, intervention_handler=...)` |
| `complete` | `summary`, `reasoning` | End run loop, `close_conversation()` |

Intervention decisions map to `InterventionResponse` during `execute_turn`.

## Execution Loop

```text
start_conversation()
loop:
  context ← build_context()
  action ← DecisionPolicy.decide(context)
  if action == complete: break
  execute_turn(message, intervention_handler)
close_conversation()
return ControllerRunResult
```

Limits: `ControllerConfig.max_turns`, `ControllerConfig.max_decisions`.

### Isolation rule (controller)

`controller/` must not import `client/`, `adapter/`, gRPC, or protobuf. Validation: `tests/phase6_common.py::scan_controller_isolation()`.

## Validation Results (Phase 6)

| Script | Step | Backend |
|---|---|---|
| `tests/test_phase6_context.py` | 6.1 — context construction | Unit |
| `tests/test_phase6_prompt.py` | 6.2 — prompting strategy | Unit |
| `tests/test_phase6_actions.py` | 6.3 — action generation | Unit |
| `tests/test_phase6_runtime.py` | 6.4 — controller runtime | In-memory harness |
| `tests/test_phase6_e2e_real.py` | 6.5 — end-to-end autonomous | Real Chakra + controller LLM |

Progress log: `docs/development_journal.md`

## Repository Verification (Phase 7)

`main.py` runs **one** `ConversationRunner` session. Chakra owns plan → implement →
verify → repair. Python keeps the conversation alive, auto-approves tools, and
sends phase-aware resume nudges (`controller/resume_nudges.py`) when verification
fails or PASS is rejected (e.g. missing `RUNTIME_CHECK: PASS`).

### Verification workflow

```text
main.py
  └─ ConversationRunner (single Chakra conversation)
        Plan → general-purpose (env + implement)
          → verification
               ├─ VERDICT: PASS + RUNTIME_CHECK: PASS → done
               └─ FAIL / rejected PASS
                    → Plan (repair_plan.md) → general-purpose repair
                    → verification again
        Artifacts: experiments/<workdir>/, logs/<run_id>/pipeline/
```

### Controller isolation

| Property | Value |
|---|---|
| Policy | `SupervisorPolicy` (thin; Chakra owns sequencing) |
| Conversation | One persistent Chakra `session_id` |
| Trace (working) | `logs/<id>/pipeline/working/trace.jsonl` |
| Trace (artifact) | `logs/<id>/pipeline/trace.jsonl` |
| Working directory | `experiments/<workdir>/` |

### Verification prompt

Built by `verification/prompts.py::build_unified_pipeline_objective()`. Phase
nudge text reuses builders in `controller/verification_workflow.py`.

### Verification verdict

Parsed by `verification/parser.py::parse_verdict()` from **subagent tool evidence only** (not main-agent prose). PASS also requires `RUNTIME_CHECK: PASS`.

| Verdict | Behaviour |
|---|---|
| `PASS` (accepted) | Exit 0 |
| `FAIL` / rejected PASS | Repair / re-verify nudges or exit 1 at limits |
| Missing | Exit 1 |

### Verification artifacts

```text
experiments/<workdir>/          # generated project files

logs/<run_id>/
└── pipeline/
    ├── working/trace.jsonl
    ├── summary.json
    ├── trace.jsonl
    └── raw_events.jsonl
```

### verification/ package

```text
verification/
├── prompts.py   # build_unified_pipeline_objective()
├── parser.py    # parse_verdict(), RUNTIME_CHECK gates
└── report.py    # save_pipeline_artifacts(), etc.
```

| Test script | Coverage |
|---|---|
| `tests/test_verification_workflow.py` | Verification/repair message builders |
| `tests/test_lifecycle.py` | Lifecycle + resume nudges |
| `tests/test_phase7_verification.py` | Parser, unified prompt, artifact storage |

CLI: `python main.py "<objective>"` (full lifecycle). Use `--skip-verification` for generation only.

See [`HANDOVER.md`](HANDOVER.md) for operator runbook.

