# EpochLedger (Rust) — Multi-Tenant Isolation

**Variant:** `v05_rust_student-hacker_multi-tenant-isolation`

Offline-first ML experiment journal. Tenants stay isolated in memory; each tenant can record experiment scores and promote a champion.

## Quick start

```bash
# from this directory
cargo build
cargo run -- tenant add alice
cargo run -- experiment run --tenant alice --name run-1 --score 0.85
cargo run -- experiment list --tenant alice
cargo run -- experiment promote-champion --tenant alice
cargo run -- tenant list
```

Platform / how to run: **CLI only** (no browser). Use the commands above from the repo root after installing a Rust toolchain (`rustup`).

## Smoke test

```bash
python scripts/smoke.py
```

Exits `0` when tenant create/list, experiment run/list, and champion promotion succeed.

## Seed data

`fixtures/seed.json` — sample tenants (`alice`, `bob`) and metrics for demos/docs.

## License

MIT
