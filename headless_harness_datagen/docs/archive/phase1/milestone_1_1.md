# Milestone 1.1 — Environment Setup

**Date:** 2026-07-01  
**Status:** Complete

## Objective

Create the repository structure for Phase 1, configure the Python environment, register the local Chakra backend location, and verify prerequisites for running Chakra.

## Implementation

### Repository structure (outside `harness/chakra`)

```text
headless_harness/
├── client/                 # Phase 1 Python gRPC client
│   ├── proto/chakra.proto  # Local copy of Chakra proto (read-only source in chakra/)
│   ├── generated/          # Python stubs from protoc
│   ├── chakra_client.py
│   ├── session.py
│   ├── config.py
│   └── mock_server.py      # Offline mock for client development
├── config/chakra.yaml      # Backend path and gRPC settings
├── scripts/                # Verification and test scripts
├── docs/phase1/            # Milestone documentation
├── logs/                   # JSON run logs from scripts
└── pyproject.toml
```

### Python environment

- Python 3.10+ with `grpcio`, `grpcio-tools`, `protobuf`, `pyyaml`
- Virtual environment: `.venv` at repo root
- Install: `pip install -e ".[dev]"`

### Chakra backend registration

`config/chakra.yaml` points to `harness/chakra` without modifying any files inside that directory:

| Setting | Value |
|---------|-------|
| Root | `harness/chakra` |
| gRPC host | `localhost` |
| gRPC port | `50051` |
| Proto source | `harness/chakra/src/proto/chakra.proto` |
| Start command | `bun run dev:grpc` (from chakra root) |

Environment overrides: `CHAKRA_GRPC_HOST`, `CHAKRA_GRPC_PORT`.

## Validation

```bash
source .venv/bin/activate
python scripts/verify_chakra.py
```

Checks performed:

- Chakra directory and key files exist (`server.ts`, `chakra.proto`, `package.json`)
- Local proto copy exists under `client/proto/`
- Python version >= 3.10
- `node_modules` present in Chakra
- Bun availability (warning if missing)
- Node.js >= 20 (warning if shell uses older node; Homebrew path noted)

Log output: `logs/verify_chakra_*.json`

## Observations

- Chakra requires **Bun** and **Node.js >= 20** to run the gRPC server. The Python client can be developed and tested independently using `client/mock_server.py`.
- No files under `harness/chakra` were modified.

## Conclusions

Phase 1 development lives entirely outside Chakra. Configuration references Chakra as a read-only backend dependency.
