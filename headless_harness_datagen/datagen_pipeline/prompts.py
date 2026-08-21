"""Thin Chakra paste prompts — NEVER dump all-10 forged files."""

from __future__ import annotations

from datagen_pipeline.paths import CHAKRA_DIR, NEXT_PROMPT_PATH, ensure_pipeline_dirs
from datagen_pipeline.queue import QueueItem

PACE = {
    "low": (
        "PACE low: ship a COMPLETE working product in few files. "
        "Target under ~20 tool calls. No gold-plating. No research."
    ),
    "medium": (
        "PACE medium: solid multi-feature MVP. "
        "Build continuously; no docs tours; no hours of cargo/npm debugging loops."
    ),
    "hard": (
        "PACE hard: full acceptance depth, still build-first. "
        "If a toolchain fails once, switch to a faithful alternate that keeps "
        "language_family + UI lock (document the swap) - do not burn an hour on installs."
    ),
}

LANG_HINT = {
    "python": "Use Python 3 as locked. Prefer stdlib/flask/fastapi. Do not rewrite in JS.",
    "typescript": "Use TypeScript as locked. Vite/Node OK. Do not rewrite in Python.",
    "javascript": "Use JavaScript/Node as locked. Do not rewrite in Python.",
    "go": "Use Go as locked. Single module under workdir. Do not rewrite in Python.",
    "rust": "Use Rust as locked. If cargo fails once, ship Go/Python twin that matches API+UI and note swap in README — still DONE only if demo works.",
    "java": "Use Java as locked (Maven/Gradle wrapper in-repo). Do not rewrite in Python.",
    "csharp": "Use C# as locked (.NET). Do not rewrite in Python.",
    "cpp": "Use C++ as locked, or thin C++ core + HTML UI if desktop is hard. Do not default to Python.",
    "excel_office": "Deliver Excel/Office workbook artifact as locked plus thin ops UI.",
}


def thin_task_prompt(item: QueueItem, *, remaining: int, model: str = "kimi3") -> str:
    abs_prompt = item.platform_prompt
    workdir = f"harness/chakra/{item.workdir}"
    cx = (item.complexity or "medium").lower()
    pace = PACE.get(cx, PACE["medium"])
    lang = item.language_runtime or "python"
    lang_line = LANG_HINT.get(lang, f"Honor language_runtime={lang} exactly.")
    if (item.ui_surface or "") == "react_spa" and lang == "python":
        lang_line = (
            "Python backend + React/Vite SPA frontend (ui_surface=react_spa). "
            "Do not ship a Python-only CLI."
        )
    return f"""# CHAKRA NEXT TASK ONLY - paste this entire block (model: {model})

Plan mode OFF. No questions. No plan-only.
Ignore red Stop-hook error / AUTO-CONTINUE - that is intentional.

## Dimension LOCK (mandatory - synthetic variety)
- language_runtime: {lang}
- ui_surface: {item.ui_surface}
- persistence: {item.persistence}
- complexity: {item.complexity}
- {lang_line}

## Pace / anti-stall
- {pace}
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
  experiments/{item.workdir}/platform_prompt.md
  (source: {abs_prompt} — do not Read artifacts/ paths; sandbox returns empty errors)
- Implement under {workdir}/ (create if missing). Prefer finishing existing code there.
- Keep calling tools until the demo runs (browser URL or CLI as PRD locks).
- Then print EXACTLY:
  DONE {item.task_key}: {item.title} - path + how to run
- PIPELINE MODE: after DONE, STOP. Do not open the next PRD yourself.
- Remaining after this: ~{remaining}

## Identity
- task_key: {item.task_key}
- category: {item.category}
- variant: {item.variant or "base"}

Start now: open the platform_prompt.md path above and implement.
"""


def write_next_prompt(item: QueueItem, *, remaining: int, model: str = "kimi3") -> str:
    ensure_pipeline_dirs()
    text = thin_task_prompt(item, remaining=remaining, model=model)
    NEXT_PROMPT_PATH.write_text(text, encoding="utf-8")
    side = CHAKRA_DIR / "CHAKRA_NEXT_TASK.md"
    try:
        side.write_text(text, encoding="utf-8")
    except OSError:
        pass
    # Signal Stop hook: after DONE <cat>:<nn>, allow stop (outer pipeline resumes).
    mode = CHAKRA_DIR / ".claude" / "datagen-pipeline.mode"
    try:
        mode.parent.mkdir(parents=True, exist_ok=True)
        mode.write_text(
            f"task_key={item.task_key}\nmodel={model}\n", encoding="utf-8"
        )
    except OSError:
        pass
    return text
