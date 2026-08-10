# Milestone 1.3 — Minimal Client

**Date:** 2026-07-01  
**Status:** Complete

## Objective

Build the thinnest possible Python client: connect, send a simple request, receive and parse the response, validate streaming behaviour.

## Implementation

### Core client (`client/chakra_client.py`)

| Method | Purpose |
|--------|---------|
| `connect()` | Open insecure channel, wait until ready |
| `open_stream()` | Start `Chat` bidi stream |
| `send_chat_request()` | Send `ChatRequest` |
| `send_user_input()` | Reply to `action_required` |
| `send_cancel()` | Send `CancelSignal` |
| `iter_events()` | Yield normalized `ServerEvent` objects |
| `chat()` | One-shot helper (open → send → consume → close) |

### Event normalization (`ServerEvent`)

All server `oneof` variants are mapped to `EventType` enum values for logging and downstream use.

### Test script

`scripts/test_minimal_chat.py`:

- Connects to configured address
- Opens stream, sends `ChatRequest`
- Prints `text_chunk` tokens as they arrive
- Auto-replies `yes` to `action_required` (tool approval)
- Stops on `done` or `error`
- Writes JSON log to `logs/minimal_chat_*.json`

## Validation

Against mock server:

```bash
# Terminal 1
python -m client.mock_server

# Terminal 2
python scripts/test_minimal_chat.py --mock
```

**Observed event sequence:**

```text
text_chunk (multiple) → done
```

**Sample output:**

```text
Echo: Say hello in one short sentence.
```

Against real Chakra (requires LLM provider configured in Chakra):

```bash
python scripts/test_minimal_chat.py --message "Say hello in one short sentence."
```

Expected additional events when tools run: `tool_start`, `action_required`, `tool_result`.

## Observations

- Streaming works: multiple `text_chunk` events precede `done.full_text`.
- Real Chakra may emit `action_required` for every tool call; client must respond with `UserInput` before the turn completes.
- Only one in-flight `ChatRequest` per stream is allowed; server returns `ALREADY_EXISTS` otherwise.

## Conclusions

Minimal programmatic chat over gRPC is working. The client is intentionally thin — no abstractions beyond event parsing and stream management.
