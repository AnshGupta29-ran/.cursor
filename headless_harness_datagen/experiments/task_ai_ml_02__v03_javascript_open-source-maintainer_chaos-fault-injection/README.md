# EpochLedger (v03_javascript_open-source-maintainer_chaos-fault-injection)

**Offline‑first ML experiment journal** that stores experiment runs in CSV files and provides a tiny CLI/TUI for interaction.  The variant adds **chaos‑style fault injection** – random corruption of CSV rows – to let open‑source maintainers see how their tooling behaves under data‑integrity stress.

## Features
- Record experiments: name, parameters (JSON string), metric value.
- Persist to `data/experiments.csv` (simple CSV, human‑readable).
- CLI (`npm start`) lets you list, add, or delete experiments.
- Fault injection: on each write a configurable 10 % chance flips a character in the CSV line, simulating disk‑corruption or bad merges.
- Seed data provided in `fixtures/experiments_seed.csv`.
- Smoke test (`npm run smoke`) runs a quick add‑list‑delete cycle and exits with code 0 if no uncaught error occurs.

## Prerequisites
- Node ≥ 14 (supports ES modules).

## Installation & Running
```bash
# Clone the repo (already in your harness folder)
npm install   # no external deps, just creates node_modules for npm scripts
npm start     # launch the interactive CLI
```

## CLI Usage
```
$ npm start
EpochLedger CLI
1) List experiments
2) Add experiment
3) Delete experiment
4) Exit
Select option: 
```
Follow the prompts; all data is written to `data/experiments.csv`.

## Smoke Test
```bash
npm run smoke   # should print success and exit 0
```

## Data
- Seed CSV located at `fixtures/experiments_seed.csv`.  Run the CLI first time to copy it into `data/experiments.csv`.

## License
MIT
