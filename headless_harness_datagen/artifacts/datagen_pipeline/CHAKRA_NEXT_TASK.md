# CHAKRA NEXT TASK ONLY - paste this entire block (model: gpt)

Plan mode OFF. No questions. No plan-only.
Ignore red Stop-hook error / AUTO-CONTINUE - that is intentional.

## Dimension LOCK (mandatory - synthetic variety)
- language_runtime: python
- ui_surface: html_canvas
- persistence: json_file
- complexity: medium
- Use Python 3 as locked. Prefer stdlib/flask/fastapi. Do not rewrite in JS.

## Pace / anti-stall
- PACE medium: solid multi-feature MVP. Build continuously; no docs tours; no hours of cargo/npm debugging loops.
- Write/Edit immediately after opening the PRD. Forbidden: WebSearch, WebFetch, Explore agents, whole-repo Grep.
- At most 2 targeted reads inside the workdir before coding.
- Do NOT spend hours on package scavenger hunts. One failed toolchain attempt -> alternate, keep UI+acceptance.

## Quality bar (NOT a stub / NOT a tiny demo)
- Full happy path works: seed data, mutate state, visible result, README one-command run.
- Forbidden DONE: Cargo.toml-only, hello-world SPA, dead HTML, API with no exercise path, README-only.
- low = thin but COMPLETE product; medium/hard = multi-view / richer acceptance as PRD.
- MUST ship: `scripts/smoke.py` (or `npm run smoke`) that exits 0 proving the demo works.
- MUST ship: seed/fixture/synthetic data under `fixtures/`, `data/`, or `seed*`.
- MUST ship: README with exact how-to-run (`cargo run` / `npm start` / `python …`) AND either
  `http://localhost:PORT/` or an explicit **CLI only** note (no fake browser URLs).
- Outer pipeline runs a deterministic VALIDATE gate after DONE — stubs fail and retry.

## Hard rules
- Do NOT open or paste any CHAKRA_PASTE_ALL_10*.md.
- Open ONLY the in-repo copy after autopilot/main.py stages it:
  experiments/task_ai_ml_02__v07_python_enterprise-buyer_csv-roundtrip/platform_prompt.md
  (source: C:\Users\anshg\.cursor\headless_harness_datagen\artifacts\datagen_pipeline\expanded\ai_ml\02_v07_python_enterprise-buyer_csv-roundtrip\platform_prompt.md — do not Read artifacts/ paths; sandbox returns empty errors)
- Implement under harness/chakra/task_ai_ml_02__v07_python_enterprise-buyer_csv-roundtrip/ (create if missing). Prefer finishing existing code there.
- Keep calling tools until the demo runs (browser URL or CLI as PRD locks).
- Then print EXACTLY:
  DONE ai_ml:02__v07_python_enterprise-buyer_csv-roundtrip: ML experiment tracking (MLflow-like) [v07_python_enterprise-buyer_csv-roundtrip] - path + how to run
- PIPELINE MODE: after DONE, STOP. Do not open the next PRD yourself.
- Remaining after this: ~0

## Identity
- task_key: ai_ml:02__v07_python_enterprise-buyer_csv-roundtrip
- category: ai_ml
- variant: v07_python_enterprise-buyer_csv-roundtrip

Start now: open the platform_prompt.md path above and implement.
