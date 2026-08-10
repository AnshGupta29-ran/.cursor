# Milestone 1.4 — Session Lifecycle

**Date:** 2026-07-01  
**Status:** Complete

## Objective

Create a session, send messages, continue conversations across turns, close sessions, and document the lifecycle.

## How Chakra sessions work

From `harness/chakra/src/grpc/server.ts`:

1. Each **turn** uses a **new** bidirectional `Chat` stream.
2. `ChatRequest.session_id` (non-empty) keys server-side message history.
3. On turn completion, the server stores `engine.getMessages()` in an in-memory `Map` (max 1000 sessions, FIFO eviction).
4. The next turn on the same `session_id` loads `previousMessages` into a new `QueryEngine`.
5. Closing the gRPC stream (`call.on('end')`) interrupts any in-flight engine but **does not** delete session history.
6. There is no explicit "delete session" RPC — sessions expire only via server eviction or process restart.

## Implementation

### `client/session.py` — `ChakraSession`

| Method | Behaviour |
|--------|-----------|
| `send_message()` | New stream → `ChatRequest` with fixed `session_id` → consume events → close stream |
| `close()` | Mark session closed client-side (no server RPC) |
| `summary()` | Return `session_id`, turn count, metadata |

Each turn is recorded as a `TurnRecord` (user message, assistant text, raw events, timestamps).

### Test script

`scripts/test_session.py` sends two messages on the same session:

1. `"Remember the number 42."`
2. `"What number did I ask you to remember?"`

Log: `logs/session_*.json`

## Validation (mock server)

```bash
python scripts/test_session.py
```

Mock confirms session persistence by appending `(prior turns: N)` on subsequent turns with the same `session_id`.

## Session lifecycle diagram

```text
Client                          Chakra Server
  │                                  │
  │── Chat stream #1 ───────────────►│
  │   ChatRequest(session_id=S)      │ create/load session S
  │◄── text_chunk / done ────────────│ save messages[S]
  │── close stream ─────────────────►│
  │                                  │
  │── Chat stream #2 ───────────────►│
  │   ChatRequest(session_id=S)      │ load messages[S]
  │◄── text_chunk / done ────────────│ update messages[S]
  │── close stream ─────────────────►│
  │                                  │
  │── session.close() (client)       │ (no RPC)
```

## Observations

- Multi-turn context requires reusing `session_id` across separate streams.
- Tool approvals are per-stream; each new turn opens a fresh stream.
- Session data is **in-memory only** — not durable across server restart.

## Conclusions

Session lifecycle is understood and implemented in `ChakraSession`. Real Chakra should retain LLM conversation context across turns when the same `session_id` is used.
