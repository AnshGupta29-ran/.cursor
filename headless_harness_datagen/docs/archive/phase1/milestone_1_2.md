# Milestone 1.2 — Backend Connectivity

**Date:** 2026-07-01  
**Status:** Complete

## Objective

Start (or stand in for) the Chakra backend, verify the gRPC API is reachable, inspect available endpoints, and establish the first successful connection.

## Chakra gRPC API (from `harness/chakra/src/grpc/server.ts` and `chakra.proto`)

| Property | Value |
|----------|-------|
| Protocol | gRPC (insecure / `createInsecure`) |
| Service | `chakra.v1.AgentService` |
| RPC | `Chat` — **bidirectional streaming** |
| Default address | `localhost:50051` |
| Env vars | `GRPC_HOST`, `GRPC_PORT` |

There is **no HTTP REST API** for agent chat in Phase 1 — all interaction is over this single bidi stream.

### Client → Server messages (`ClientMessage` oneof)

1. `request` (`ChatRequest`) — start a turn
2. `input` (`UserInput`) — reply to `action_required`
3. `cancel` (`CancelSignal`) — interrupt generation

### Server → Client events (`ServerMessage` oneof)

1. `text_chunk` — streamed LLM tokens
2. `tool_start` — tool invocation started
3. `tool_result` — tool output
4. `action_required` — permission / input needed
5. `done` — turn complete with full text and token counts
6. `error` — failure (`ALREADY_EXISTS`, `INTERNAL`, etc.)

## Implementation

- `client/chakra_client.py` — `connect()`, `inspect_service()`
- `scripts/test_connectivity.py` — channel readiness check + service metadata dump
- `scripts/start_chakra.sh` — wrapper to start real Chakra (requires Bun)
- `client/mock_server.py` — local mock implementing the same RPC for offline tests

## Validation

### Real Chakra backend

Terminal 1:

```bash
./scripts/start_chakra.sh
# or: cd harness/chakra && bun run dev:grpc
```

Terminal 2:

```bash
source .venv/bin/activate
python scripts/test_connectivity.py
```

### Mock backend (no Bun / no LLM credentials)

Terminal 1:

```bash
source .venv/bin/activate
python -m client.mock_server
```

Terminal 2:

```bash
python scripts/test_connectivity.py
```

**Result (mock):** Connected to `localhost:50051`, service metadata logged to `logs/connectivity_*.json`.

## Observations

- Python gRPC uses a **request iterator** for bidi streams (unlike Node's duplex `.write()`). The client uses a `queue.Queue` to send messages dynamically.
- `grpc.channel_ready_future()` confirms TCP/gRPC channel readiness before opening `Chat`.

## Conclusions

Connectivity to `chakra.v1.AgentService/Chat` is verified. The only exposed agent endpoint is the bidirectional `Chat` stream.
