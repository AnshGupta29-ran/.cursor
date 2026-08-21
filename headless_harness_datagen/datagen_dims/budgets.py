"""Depth / fidelity guidance keyed by complexity (low|medium|hard).

IMPORTANT: Do NOT tell agents to stop early for time. Wall-clock fields below
are for automated harness timeouts only — interactive Chakra pastes use
depth_prompt_line() which forbids turn/time caps.
"""

from __future__ import annotations

from typing import Any

COMPLEXITY_BUDGETS: dict[str, dict[str, Any]] = {
    "low": {
        "wall_clock_timeout_minutes": 90,
        "max_turns": 160,
        "max_decisions": 160,
        "max_repair_iterations": 2,
        "progress_timeout_minutes": 40,
        "forge_scope": "thin MVP — few files, minimal polish, but every primary action must work end-to-end",
        "ui_fidelity": "LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form",
        "expected_effort": "typically thinner than medium/hard (fewer files & screens), but never stop early",
        "anti_stub": "FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups",
        "anti_search": "Build-first: no WebSearch/WebFetch/docs tours/winget-search installs; ≤2 local Greps then Write — low tasks must ship in few files",
    },
    "medium": {
        "wall_clock_timeout_minutes": 120,
        "max_turns": 240,
        "max_decisions": 240,
        "max_repair_iterations": 3,
        "progress_timeout_minutes": 50,
        "forge_scope": "solid MVP — core features + light tests/smoke, avoid gold-plating",
        "ui_fidelity": "MEDIUM — clear multi-panel layout, core interactions that mutate state, seeded demo data, light charts if required",
        "expected_effort": "deeper than low; still ship demoable without endless polish",
        "anti_stub": "FORBIDDEN as DONE: single bare form, API with no operator console, static HTML that does not call live endpoints",
        "anti_search": "Build-first: implement from PRD; forbid WebSearch/WebFetch and repo-wide fishing; code > research",
    },
    "hard": {
        "wall_clock_timeout_minutes": 150,
        "max_turns": 320,
        "max_decisions": 320,
        "max_repair_iterations": 4,
        "progress_timeout_minutes": 60,
        "forge_scope": "full PRD depth — richer acceptance criteria and verification",
        "ui_fidelity": "HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable",
        "expected_effort": "deepest; more entities, edges, and verification — still no wall-clock stop",
        "anti_stub": "FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths",
        "anti_search": "Build-first still applies: no online research loops; deepen the product with Write/Edit, not Explore agents",
    },
}

# Preferred UI surfaces by complexity (graphics/fidelity ladder for non-game cats)
UI_BY_COMPLEXITY: dict[str, list[str]] = {
    "low": ["static_html", "cli_tui", "api_only", "desktop_window"],
    "medium": ["html_canvas", "static_html", "dashboard_charts", "mobile_web"],
    "hard": ["react_spa", "html_canvas", "dashboard_charts", "desktop_window", "game_loop_window"],
}


def budget_for(complexity: str | None) -> dict[str, Any]:
    key = (complexity or "medium").strip().lower()
    if key not in COMPLEXITY_BUDGETS:
        key = "medium"
    return dict(COMPLEXITY_BUDGETS[key])


def depth_prompt_line(complexity: str | None) -> str:
    """Interactive paste line — depth + fidelity, explicitly no turn/time stop."""
    key = (complexity or "medium").strip().lower()
    if key not in COMPLEXITY_BUDGETS:
        key = "medium"
    b = COMPLEXITY_BUDGETS[key]
    anti = b.get("anti_stub") or ""
    anti_search = b.get("anti_search") or (
        "Build-first: no WebSearch/WebFetch; Write from the PRD."
    )
    return (
        f"**Depth ({key}):** {b['forge_scope']}. "
        f"**UI fidelity:** {b['ui_fidelity']}. "
        f"**Effort cue:** {b['expected_effort']}. "
        f"{anti} "
        f"{anti_search} "
        f"**No wall-clock or turn limit** — keep calling tools until demoable, then continue. "
        f"Honor the dimensions JSON (language/UI/persistence/verification) exactly."
    )


def budget_prompt_line(complexity: str | None) -> str:
    """Alias used by assemble/forge — always the non-stopping depth line."""
    return depth_prompt_line(complexity)


def align_ui_to_complexity(hint: dict[str, Any]) -> dict[str, Any]:
    """If UI surface conflicts with complexity ladder, nudge it into band."""
    out = dict(hint)
    cx = str(out.get("complexity") or "medium").lower()
    if cx not in UI_BY_COMPLEXITY:
        cx = "medium"
    preferred = UI_BY_COMPLEXITY[cx]
    ui = str(out.get("ui_surface") or "")
    # low must not keep heavy SPA; hard should not stay api_only unless artifact is backend
    artifact = str(out.get("artifact_type") or "")
    if cx == "low" and ui in {"react_spa", "game_loop_window", "dashboard_charts"}:
        out["ui_surface"] = preferred[0]
    elif cx == "hard" and ui in {"api_only", "cli_tui"} and "backend" not in artifact and "cli" not in artifact:
        out["ui_surface"] = preferred[0]
    elif cx == "medium" and ui in {"game_loop_window"}:
        out["ui_surface"] = "html_canvas"
    return out
