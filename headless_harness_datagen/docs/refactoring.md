# Refactoring the Orchestration to Follow Chakra's Natural Execution Flow

## Goal

Refactor the orchestration layer so that repository generation is driven entirely by Chakra's native conversation lifecycle.

The Python orchestration layer should become a transparent execution supervisor whose responsibilities are limited to:

- starting a single Chakra conversation
- approving tool requests
- streaming conversation events
- collecting execution traces
- monitoring session health
- detecting terminal completion markers
- shutting down cleanly

All implementation, verification, repair, and re-verification decisions must be delegated to Chakra.


The final architecture should consist of a **single long-lived Chakra conversation** that owns the complete repository generation lifecycle.

```
Python

↓

ConversationRunner

↓

Single Chakra Session

↓

Approve Tool Requests

↓

Collect Traces

↓

Watch Conversation Events

↓

Detect Completion Marker

↓

End Conversation
```

The Python orchestrator should become a thin execution supervisor rather than an active workflow controller.

---

# Phase 1 — Simplify the Architecture

## Objective

Replace the current multi-session orchestration with a single persistent Chakra conversation.
The existing orchestration state machine should be removed.
The Python layer should no longer manage separate implementation, verification, repair, or planning sessions.

Instead, it should only:

- create one conversation
- continuously approve tool requests
- stream conversation events
- collect traces
- detect completion
- terminate cleanly

The conversation itself should own the entire workflow.

---

## Required Changes
Remove orchestration logic that manually starts separate agent sessions.
Remove workflow state transitions such as:
```
Generation
↓
Verification
↓
Repair
↓
Verification
```

Replace them with a single persistent conversation.

Conversation ownership should move entirely into Chakra.

---

## Acceptance Criteria
Python creates exactly one Chakra conversation.
The conversation remains alive until explicit completion.
Python never creates a second implementation or verification session.
---

# Phase 2 — Build the Conversation Runner

## Objective
Create a dedicated ConversationRunner responsible for the lifetime of one Chakra conversation.
This component becomes the central execution loop.
---
## Responsibilities
ConversationRunner should:
- start one conversation
- receive streamed events
- approve tool requests
- collect traces
- monitor session health
- detect completion markers
- terminate gracefully

It should not contain generation-specific logic. It should only supervise conversation execution.

---
## Conversation Ownership Principle

Once a conversation has been started, the Python orchestration should never attempt to steer the workflow.
Python observes.
Chakra decides.
Python terminates only when Chakra reaches a terminal state or when the orchestration detects unrecoverable stagnation or cancellation.
---

## Acceptance Criteria

ConversationRunner becomes the single entry point for all repository generation.
No other component directly manages conversation execution.

---

# Phase 2.5 — Long-Running Session Management

## Objective

Support extremely long-running repository generation without premature timeout.
Repository generation may legitimately take tens of minutes or hours depending on:
- repository size
- backend model latency
- local models
- verification duration
- repair iterations
- build duration
The orchestration must remain connected for the lifetime of the conversation.
---

## Long-Running Execution Principle

Repository generation is an interactive conversation rather than a request-response API call.
The orchestration should remain connected until:
- completion
- unrecoverable error
- explicit cancellation
- confirmed stagnation
Never terminate simply because the conversation has been running for a long time.

---

## Replace Fixed Timeouts
Do not use fixed execution limits such as:
- 5 minutes
- 10 minutes
- 30 minutes
Avoid overall wall-clock timeouts.

---

## Inactivity Timeout
Maintain an inactivity timer.
Reset it whenever the conversation produces any activity such as:
- streamed assistant output
- tool request
- tool response
- agent lifecycle event
- heartbeat
- conversation state update
Terminate only after prolonged inactivity.

---

## Distinguish Liveness from Progress
The orchestrator must distinguish between:
### Liveness
The conversation is still alive.
Examples:
- assistant messages
- streamed tokens
- tool requests
- tool responses
- heartbeat events
- agent spawn
- agent completion
Liveness alone should never justify keeping a session alive forever.

---

### Forward Progress
The conversation is moving toward completion.
Examples:
- implementation work completed
- files created
- files modified
- TODO items completed
- successful tool execution
- verification started
- verification completed
- repair completed
- completion markers emitted
Forward progress should reset the progress timer.
---

## Progress Timeout
Maintain a separate progress timeout.
If the conversation remains alive but makes no forward progress for a configurable period, consider it stagnant.

Do not terminate immediately.

Instead begin stagnation handling.

---

## Detect Repeated Failures

Track repeated identical failures.

Examples:

- repeated permission errors
- repeated invalid tool calls
- repeated malformed Agent requests
- repeated execution failures using the same arguments

If the same failure repeats beyond a configurable threshold, treat the session as stuck.

---

## Stagnation Handling

Use staged escalation.

```
Healthy

↓

Stagnation Detected

↓

Warning

↓

Continue Monitoring

↓

Repeated Failure Threshold

↓

Graceful Termination

↓

Collect Traces
```

Do not terminate immediately after the first repeated error.

---

## Configuration

Expose all limits through configuration.

Example:

```python
ConversationConfig(
    inactivity_timeout_minutes=60,
    progress_timeout_minutes=20,
    repeated_failure_threshold=8,
)
```

Never hardcode timeout values.

---

## Acceptance Criteria

Large repositories and slow local models can run for hours without timeout.

Only inactive or genuinely stuck conversations terminate automatically.

---

# Phase 3 — Event-Driven Execution

## Objective

Drive orchestration entirely through Chakra events.

The Python layer should never poll conversation state.
The event loop must never restart the conversation in response to intermediate events.
A conversation should remain active until an explicit terminal condition is reached.
---

## Event Loop

ConversationRunner should continuously wait for streamed events.

Process each event as it arrives.

The event loop should be blocking and event-driven.

Never implement polling loops with fixed execution windows.

---

## Event Processing

Process:

- assistant responses
- tool requests
- tool responses
- agent lifecycle events
- streamed tokens
- completion markers
- errors

Each event should immediately update orchestration state.

---

## Acceptance Criteria

ConversationRunner reacts exclusively to streamed events.

No polling logic exists.

---

# Phase 4 — Automatic Tool Approval

## Objective

Approve tool requests automatically while collecting execution traces.
Python should act as a transparent supervisor.
Tool approval must remain stateless.
The orchestrator should not alter approval behavior based on the current implementation stage.
Tool approval is independent of planning, implementation, verification, or repair.

---

## Responsibilities

Approve valid tool requests.

Capture:

- request
- response
- timestamps
- tool metadata

Continue streaming immediately.

Do not introduce workflow decisions during tool approval.

---

## Acceptance Criteria

Every approved tool call appears in the trace.

Tool approval never blocks conversation flow.

---

# Phase 5 — Trace Collection

## Objective

Collect every conversation event into a complete execution trace.
Store both:
- raw Chakra events
- normalized orchestration traces
Raw events should always be preserved to allow replay, debugging, and future parser improvements.
---

## Capture

Store:

- assistant messages
- reasoning events (if available)
- tool requests
- tool responses
- agent lifecycle events
- verification results
- timestamps
- completion markers

Preserve ordering exactly.

---

## Acceptance Criteria

A complete replay of the conversation can be reconstructed from the trace.

---

# Phase 6 — Completion Detection

## Objective

Detect when the conversation has naturally completed.

Python should never guess completion.

---

## Completion Sources

Completion should be determined using explicit conversation markers such as:

- IMPLEMENTATION_STATUS: COMPLETE
- VERDICT: PASS
- REPAIR_STATUS: COMPLETE
- other defined completion markers
Completion should be determined only from explicit terminal conversation events.
The orchestrator must never infer completion from inactivity, absence of tool requests, or lack of new messages.
Terminal completion should be driven by the final conversation state produced by Chakra.

End the conversation only after receiving the expected terminal marker.

---

## Acceptance Criteria

Conversation termination is deterministic.

No heuristic completion detection exists.

---

# Phase 7 — Delegate Verification and Repair Loop to Chakra

## Objective

The Python orchestration must not implement generation, verification, or repair loops.

Instead, it should allow Chakra's main conversation to manage the complete implementation lifecycle.

The Python layer should remain an execution supervisor.

---

## Expected Conversation Flow

The conversation should naturally evolve as:

Main Agent

↓

Implementation

↓

Verification Agent

↓

PASS

or

Main Agent

↓

Implementation

↓

Verification Agent

↓

FAIL

↓

Main Agent (or General-Purpose Agent)

↓

Repair

↓

Verification Agent

↓

FAIL

↓

Repair

↓

Verification Agent

↓

PASS

This loop should continue until:

- VERDICT: PASS
- unrecoverable failure
- explicit cancellation
- configured repair iteration limit

---

## Python Responsibilities

The Python orchestrator should:

- keep the conversation alive
- approve tool requests
- stream events
- collect traces
- observe verification verdicts
- detect completion markers

The orchestrator must never manually restart generation, verification, or repair sessions.

---

## Chakra Responsibilities

The Chakra conversation owns:

- implementation
- verification
- repair
- repeated verification
- deciding when work is complete

Python should treat these as ordinary conversation events.

---

## Acceptance Criteria

Repository generation, verification, repair, and re-verification all occur within the same Chakra conversation.

Python never creates a second conversation to continue the workflow.

The conversation terminates only after:

- VERDICT: PASS,
- unrecoverable failure,
- user cancellation,
- or configured maximum repair iterations.


---

# Final Architecture

```
Python

↓

ConversationRunner

↓

Single Chakra Conversation

↓

Approve Tool Requests

↓

Collect Events

↓

Collect Traces

↓

Monitor Session Health

↓

Watch Completion Marker

↓

Graceful Shutdown
```

Python acts only as the execution supervisor.

Chakra owns the complete repository generation workflow.

The orchestration remains active for the lifetime of the conversation, regardless of execution duration, and only terminates upon explicit completion, unrecoverable error, user cancellation, or confirmed stagnation.