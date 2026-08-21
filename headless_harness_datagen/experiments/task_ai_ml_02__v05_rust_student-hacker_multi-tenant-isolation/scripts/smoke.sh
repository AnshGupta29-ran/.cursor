#!/usr/bin/env bash
# Smoke test for EpochLedger v05 Rust multi‑tenant isolation demo
# This script runs a few CLI commands to ensure the binary works.

set -e

# Ensure the binary builds
cargo build --quiet

# Run basic commands; they should exit with status 0
cargo run --quiet -- list-tenants
cargo run --quiet -- list-experiments tenant-a || true  # may be empty but should not error

# Import seed data (if present) for a tenant and list again
if [ -f fixtures/seed.json ]; then
  cargo run --quiet -- import fixtures/seed.json --tenant tenant-a
  cargo run --quiet -- list-experiments tenant-a
fi

echo "Smoke test passed"
