# Phase 1 Knowledge Base — Chakra Backend Protocol

Permanent technical reference for the Chakra gRPC backend as used by the headless harness (Phase 1).

**Sources (read-only):**

- `harness/chakra/src/proto/chakra.proto` (identical to `openclaude.proto` in this repo)
- `harness/chakra/src/grpc/server.ts`
- `harness/chakra/scripts/start-grpc.ts`

---

## Startup sequence

1. **Prerequisites:** Bun, Node.js >= 20, Chakra dependencies installed (`node_modules` in `harness/chakra`).
2. **Provider configuration:** Chakra loads LLM provider profile from env / secure storage (`start-grpc.ts` calls `validateProviderEnvOrExit()`).
3. **Start server:**

   ```bash
   cd harness/chakra
   bun run dev:grpc
   ```

   Or from repo root: `./scripts/start_chakra.sh`

4. **Environment:**

   | Variable | Default | Description |
   |----------|---------|-------------|
   | `GRPC_HOST` | `localhost` | Bind address |
   | `GRPC_PORT` | `50051` | Listen port |

5. **Confirmation:** Log line `gRPC Server running at localhost:50051` (from `server.ts`).

6. **Client override:** `CHAKRA_GRPC_HOST`, `CHAKRA_GRPC_PORT` in the Python harness.

---

## Endpoints

| Type | Name | Description |
|------|------|-------------|
| gRPC | `chakra.v1.AgentService/Chat` | Bidirectional stream — **only** agent API |

No HTTP chat endpoints. No unary RPCs for sessions.

---

## Transport

- **Protocol:** gRPC over HTTP/2
- **Security:** Insecure credentials (no TLS, no auth in current server)
- **Pattern:** Client-streaming + server-streaming on one RPC

---

## Request / response formats

### ClientMessage (client → server)

Protobuf `oneof payload`:

```protobuf
message ClientMessage {
  oneof payload {
    ChatRequest request = 2;
    UserInput input = 3;
    CancelSignal cancel = 4;
  }
}
```

#### ChatRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | yes | User prompt for this turn |
| `working_directory` | string | no | CWD for tool execution (defaults to server CWD) |
| `model` | string | no | Override LLM model |
| `session_id` | string | no | Non-empty enables cross-stream session persistence |

#### UserInput

| Field | Type | Description |
|-------|------|-------------|
| `reply` | string | User answer (`yes`/`y` allows tool; other denies) |
| `prompt_id` | string | Must match `action_required.prompt_id` |

#### CancelSignal

| Field | Type | Description |
|-------|------|-------------|
| `reason` | string | Human-readable cancel reason |

### ServerMessage (server → client)

Protobuf `oneof event`:

| Event | When emitted |
|-------|----------------|
| `text_chunk` | LLM streaming text delta |
| `tool_start` | Before tool permission prompt |
| `tool_result` | After tool executes |
| `action_required` | Waiting for user approval (`CONFIRM_COMMAND`) or info |
| `done` | Turn finished successfully |
| `error` | Failure (e.g. `ALREADY_EXISTS`, `INTERNAL`) |

#### FinalResponse (`done`)

| Field | Description |
|-------|-------------|
| `full_text` | Complete assistant text for the turn |
| `prompt_tokens` | Input token count |
| `completion_tokens` | Output token count |

#### ErrorResponse

| Code | Meaning |
|------|---------|
| `ALREADY_EXISTS` | Second `request` on same stream while turn in progress |
| `INTERNAL` | Unhandled server exception |

---

## Streaming protocol

### Per-turn flow

```text
Client                                    Server
  │ open Chat stream                         │
  │─────────────────────────────────────────►│
  │ ClientMessage{request: ChatRequest}        │
  │─────────────────────────────────────────►│
  │◄─────────────────────────────────────────│ ServerMessage{text_chunk} × N
  │◄─────────────────────────────────────────│ ServerMessage{tool_start} (optional)
  │◄─────────────────────────────────────────│ ServerMessage{action_required} (optional)
  │ ClientMessage{input: UserInput}          │
  │─────────────────────────────────────────►│
  │◄─────────────────────────────────────────│ ServerMessage{tool_result} (optional)
  │◄─────────────────────────────────────────│ ServerMessage{done}
  │ close / end stream                       │
```

### Interruption

- Client sends `ClientMessage{cancel: CancelSignal}` → server calls `engine.interrupt()`, ends stream.
- Client closes stream → server interrupts engine, resolves pending permission prompts with `'no'`.

### Constraints

- **One active request per stream** at a time.
- **Tool approval:** Server blocks `canUseTool` until `UserInput` arrives for the matching `prompt_id`.
- **Text streaming:** Only `content_block_delta` / `text_delta` events are forwarded as `text_chunk`.

---

## Session lifecycle

| Phase | Client action | Server behaviour |
|-------|---------------|------------------|
| Create | Generate UUID `session_id`, send on first `ChatRequest` | Creates empty or loads existing entry in `sessions` Map |
| Continue | Reuse `session_id` on new stream + new `ChatRequest` | Hydrates `initialMessages` from stored history |
| Turn complete | Receive `done`, close stream | Persists `engine.getMessages()` under `session_id` |
| Close (client) | `ChakraSession.close()` | No server RPC; history remains until eviction |
| Eviction | — | Max 1000 sessions; oldest inserted key removed |
| Server restart | — | All sessions lost (in-memory only) |

---

## Implementation decisions (Phase 1)

| Decision | Rationale |
|----------|-----------|
| Python client outside `harness/chakra` | Per project rule: no Chakra modifications |
| Proto copied to `client/proto/` | Generate stubs without touching Chakra tree |
| Queue-based bidi stream in Python | Python gRPC requires request iterator, not duplex `.write()` |
| `client/mock_server.py` | Enables CI and dev without Bun/LLM credentials |
| JSON logs in `logs/` | Reproducible validation artifacts per milestone |
| No harness interface yet | Phase 1 is protocol research only (per `phase_plan.md`) |
| Auto-approve tools in tests | Unblocks scripted tests; real operator would reason over `action_required` |

---

## Related documentation

| Document | Content |
|----------|---------|
| `milestone_1_1.md` | Environment setup log |
| `milestone_1_2.md` | Connectivity validation |
| `milestone_1_3.md` | Minimal client |
| `milestone_1_4.md` | Session lifecycle |
| `../phase_plan.md` | Full multi-phase plan |
| `../sys_architecture.md` | Long-term architecture |
