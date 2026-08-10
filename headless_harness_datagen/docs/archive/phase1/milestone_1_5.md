# Milestone 1.5 — Knowledge Base

**Date:** 2026-07-01  
**Status:** Complete

## Objective

Record every endpoint, request/response formats, startup sequence, session lifecycle, streaming protocol, and implementation decisions.

## Deliverable

Consolidated reference: **[knowledge_base.md](./knowledge_base.md)**

## Contents summary

1. **Startup sequence** — Bun, provider validation, `dev:grpc`, env vars
2. **Endpoints** — Single RPC: `chakra.v1.AgentService/Chat`
3. **Message schemas** — All `ClientMessage` and `ServerMessage` variants
4. **Streaming protocol** — Per-turn event order, cancellation, constraints
5. **Session lifecycle** — Cross-stream persistence via `session_id`
6. **Implementation decisions** — Python queue pattern, mock server, no Chakra edits

## Validation

Knowledge base cross-checked against:

- `harness/chakra/src/grpc/server.ts` (runtime behaviour)
- `harness/chakra/src/proto/chakra.proto` (wire format)
- Phase 1 test logs in `logs/`

## Conclusions

Phase 1 is complete. The headless harness can programmatically communicate with Chakra over gRPC, manage multi-turn sessions, and the protocol is fully documented for Phase 2 capability analysis.
