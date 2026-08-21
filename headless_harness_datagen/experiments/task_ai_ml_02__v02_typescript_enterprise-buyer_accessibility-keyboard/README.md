# Enterprise Buyer Accessibility Keyboard – ML Experiment Tracker

## Overview

`epochledger-v02_typescript_enterprise-buyer_accessibility-keyboard` is a **low‑complexity** TypeScript demo that mimics an ML‑experiment journal (think MLflow) for an enterprise‑buyer audience.  It focuses on **accessibility** – all UI interactions can be performed purely with a keyboard.

* **Persistence** – experiments are stored in a plain JSON file (`data/experiments.json`).
* **CLI entry point** – quick one‑liner commands to *add* and *list* experiments.
* **React SPA UI** – a tiny React single‑page‑app that lists experiments and can be navigated without a mouse.
* **Seed data** – a small fixture (`fixtures/seed.json`) is copied on first run.
* **Smoke test** – `scripts/smoke.py` runs the CLI commands and exits with status 0.

## Project structure

```
src/
│   cli.ts            # CLI entry point
│   experiment.ts     # Core domain logic
│   persistence.ts    # JSON file read/write helpers
│   ui_server.ts      # Minimal HTTP server for the SPA
public/
│   index.html        # React UI (keyboard‑friendly)
fixtures/
│   seed.json         # Sample experiments
data/
│   experiments.json  # Created on first run (populated from seed)
scripts/
│   smoke.py          # Smoke test that must exit 0
package.json
tsconfig.json
README.md
```

The code stays **below the hard‑complexity threshold**: no external dependencies other than the Node standard library and the React CDN.

## Prerequisites

* Node ≥ 18 (for native ES‑module support)
* `npm` (used only for the `run` scripts, no packages are installed)

## Install / Run

```bash
# Clone / copy the repository (the repo already contains the code)
npm install   # installs dev‑only types for TypeScript, no runtime deps
```

### 1️⃣ Seed the data store

```bash
npm run seed   # copies fixtures/seed.json → data/experiments.json
```

### 2️⃣ Use the CLI

```bash
# Add a new experiment
npm run cli -- add "Keyboard navigation study"

# List all experiments
npm run cli -- list
```

### 3️⃣ Start the UI

```bash
npm run ui   # Serves http://localhost:3000 – reachable via keyboard only
```

*Tab* through the experiment list, use *Enter* on a row to view its JSON payload.

## Smoke test

```bash
python scripts/smoke.py    # should exit with status 0
```

If the smoke script finishes without error you have a **shippable demo**.

## Accessibility notes

* All interactive elements are native HTML `<button>` elements – focusable via `Tab`.
* The React app uses the `aria‑label` attribute to describe experiment rows.
* Keyboard shortcuts:
  * `Ctrl+L` – focus the filter input.
  * `Enter` – expand the selected experiment.

---

**Done** `DONE task_ai_ml_02__v02_typescript_enterprise-buyer_accessibility-keyboard`