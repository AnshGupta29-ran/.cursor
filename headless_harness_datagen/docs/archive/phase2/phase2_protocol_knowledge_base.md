# Phase 2 Protocol Knowledge Base

Consolidated technical reference for Chakra's externally visible protocol.

## API Overview

- **Service:** `chakra.v1.AgentService`
- **Operation:** `Chat(stream ClientMessage) returns (stream ServerMessage)`
- **Transport:** gRPC bidirectional streaming over insecure channel by default
- **Default Address:** `localhost:50051`

## Supported Operations

| Operation | Type | Purpose |
|---|---|---|
| `AgentService.Chat` | bidi streaming RPC | Submit turns, handle tool approvals, receive streamed output, errors, and completion |

## Request Models

`ClientMessage` oneof payload:

- `request` (`ChatRequest`)
  - `message: string`
  - `working_directory: string`
  - `model: optional string`
  - `session_id: string`
- `input` (`UserInput`)
  - `reply: string`
  - `prompt_id: string`
- `cancel` (`CancelSignal`)
  - `reason: string`

## Response Models

`ServerMessage` oneof event:

- `text_chunk` (`TextChunk.text`)
- `tool_start` (`tool_name`, `arguments_json`, `tool_use_id`)
- `tool_result` (`tool_name`, `output`, `is_error`, `tool_use_id`)
- `action_required` (`prompt_id`, `question`, `type`)
- `done` (`full_text`, `prompt_tokens`, `completion_tokens`)
- `error` (`message`, `code`)

## Event Models

- **Text streaming:** sequence of `text_chunk` events.
- **Tool workflow:** `tool_start` -> `action_required` -> `tool_result`.
- **Terminal events:** `done` for success, `error` for failure.

## Streaming Protocol

1. Client opens stream.
2. Client sends `ClientMessage.request`.
3. Server emits any combination of stream events.
4. For `action_required`, client responds with `ClientMessage.input`.
5. Server emits `done` or `error`.
6. Client closes stream.

Observed constraints:

- Only one request should be in-flight per stream.
- A new turn is typically sent on a new stream.
- `done` and `error` are terminal for a turn.

## Session Lifecycle

- Session continuity is controlled by `ChatRequest.session_id`.
- Reusing the same `session_id` on later turns rehydrates prior context.
- Session closure is client-side (`close` local object / close stream); there is no dedicated delete-session RPC.
- Session persistence is process-memory scoped in current server behavior.

## Tool Interaction

- Server announces tool invocation with `tool_start`.
- Server pauses and requests user decision via `action_required`.
- Client responds with `UserInput(prompt_id, reply)`.
- Server emits `tool_result` and continues to terminal event.

## Cancellation Behaviour

- Client sends `CancelSignal`.
- Server interrupts current processing and stream ends.
- Cancellation is best-effort and should be followed by stream teardown on client side.
- Immediate teardown can surface a transient client warning (`StatusCode.UNKNOWN: Exception iterating requests!`) depending on stream timing.

## Error Behaviour

- Errors surface as `ServerMessage.error`.
- `error` is terminal for current turn.
- Typical example codes: `INTERNAL`, `ALREADY_EXISTS` (implementation-dependent).

## Capability Matrix

| Capability | Supported | Notes |
|---|---|---|
| Bidirectional chat streaming | Yes | `AgentService.Chat` |
| Session resume/continuation | Yes | `session_id` |
| Tool approvals | Yes | `action_required` + `UserInput` |
| Tool result events | Yes | `tool_result` |
| Cancellation | Yes | `CancelSignal` |
| Explicit session delete RPC | No | Not exposed |
| Built-in auth/TLS in this server mode | No | Insecure by default |

## Observed Constraints

- API surface is intentionally minimal (single RPC).
- Operation semantics are encoded in streamed message types.
- Controller implementations must be event-driven and stateful.

## Best Practices

- Always handle `action_required`; do not assume auto-approval.
- Treat `done`/`error` as terminal markers for a turn.
- Reuse `session_id` for multi-turn continuity.
- Record full event streams for reproducibility and debugging.
- Add timeout and cancellation handling around every turn.

## Evidence

- Scripts: `scripts/test_phase2_*.py`
- Raw artifacts: `logs/phase2/*.json`
- Chronological log: `logs/phase2_execution_log.md`











Implemented Phase 2 fully with milestone-by-milestone scripts, logs, and protocol docs, all outside harness/chakra.

What I added
Phase 2 scripts (scripts/test_*.py)

scripts/test_phase2_api_surface.py (2.1)
scripts/test_phase2_models.py (2.2)
scripts/test_phase2_streaming.py (2.3)
scripts/test_phase2_session_lifecycle.py (2.4)
scripts/test_phase2_tool_interaction.py (2.5)
scripts/test_phase2_error_cancellation.py (2.6)
scripts/test_phase2_capability_summary.py (2.7)
Shared helper: scripts/phase2_common.py
Phase 2 documentation artifacts

logs/phase2_execution_log.md (chronological execution log)
docs/phase2/phase2_protocol_knowledge_base.md (consolidated protocol KB)
Phase 2 raw evidence

logs/phase2/*.json (one JSON artifact per milestone)
Mock backend enhancements for full protocol coverage

Updated client/mock_server.py to support deterministic:
tool flow (tool_start -> action_required -> tool_result)
forced error flow (error)
cancellation flow (CancelSignal path)
README updated

README.md now includes Phase 2 run commands and links to new artifacts.
Validation run
Executed all Phase 2 scripts in order successfully:

python scripts/test_phase2_api_surface.py
python scripts/test_phase2_models.py
python scripts/test_phase2_streaming.py
python scripts/test_phase2_session_lifecycle.py
python scripts/test_phase2_tool_interaction.py
python scripts/test_phase2_error_cancellation.py
python scripts/test_phase2_capability_summary.py
Outputs were generated under logs/phase2/ and summarized in logs/phase2_execution_log.md.

Notes from discovery
Public API surface is a single bidi RPC: chakra.v1.AgentService/Chat.
Request envelopes: request, input, cancel.
Event envelopes: text_chunk, tool_start, tool_result, action_required, done, error.
Session continuity is via session_id across new streams.
Tool approval loop is explicit and controller-driven.
Cancellation is best-effort; immediate teardown can emit transient gRPC warning (StatusCode.UNKNOWN).
If you want, I can now start Phase 3 and draft the backend-independent harness contract directly from this Phase 2 capability model.