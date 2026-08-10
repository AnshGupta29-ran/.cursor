"""Synthetic datagen dimension taxonomy for agentic training matrices.

Meta-level axes describe *what kind of work / world* an example sits in.
Generic (operational) axes describe *how* the harness runs it.
Every example should carry values on both layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# Band helpers (shared by complexity + value)
# ---------------------------------------------------------------------------

BANDS_LMH = ("low", "medium", "hard")


@dataclass(frozen=True)
class Dimension:
    """One axis in the datagen matrix."""

    id: str
    title: str
    layer: str  # "meta" | "generic" | "quality"
    values: tuple[str, ...]
    description: str
    # If True, included in default cross-product planning
    matrix_axis: bool = True


# ---------------------------------------------------------------------------
# META-LEVEL dimensions (what the agentic model is being trained *for*)
# ---------------------------------------------------------------------------

META_DIMENSIONS: tuple[Dimension, ...] = (
    Dimension(
        id="task_family",
        title="Task family",
        layer="meta",
        description=(
            "Primary cognitive/job type. Most generic skill axis for an "
            "agentic coding/analysis model."
        ),
        values=(
            "coding_implement",
            "coding_debug",
            "coding_refactor",
            "coding_review",
            "analysis_reason",
            "data_visualization",
            "data_wrangling",
            "research_synthesize",
            "planning_decompose",
            "testing_qa",
            "documentation",
            "devops_ops",
            "spreadsheet_excel",
            "ml_inference_eval",
            "security_audit",
            "migration_upgrade",
        ),
    ),
    Dimension(
        id="business_domain",
        title="Business / vertical domain",
        layer="meta",
        description="Industry or product vertical the task lives in.",
        values=(
            "ecommerce",
            "finance_fintech",
            "healthcare",
            "education",
            "devops_platform",
            "gaming",
            "iot_automation",
            "media_cms",
            "security_privacy",
            "productivity_collab",
            "social_comms",
            "logistics_ops",
            "legal_compliance",
            "data_analytics",
            "general_utilities",
        ),
    ),
    Dimension(
        id="artifact_type",
        title="Deliverable artifact",
        layer="meta",
        description="What kind of artifact the agent must produce or modify.",
        values=(
            "web_fullstack",
            "backend_api",
            "frontend_spa",
            "cli_tool",
            "library_sdk",
            "data_pipeline",
            "notebook_analysis",
            "spreadsheet_workbook",
            "desktop_app",
            "game_prototype",
            "infra_as_code",
            "docs_spec",
            "test_suite",
            "mixed_monorepo",
        ),
    ),
    Dimension(
        id="language_runtime",
        title="Language / runtime",
        layer="meta",
        description="Primary implementation language or office runtime.",
        values=(
            "python",
            "typescript",
            "javascript",
            "cpp",
            "csharp",
            "java",
            "go",
            "rust",
            "sql",
            "excel_office",
            "bash_shell",
            "html_css",
            "mixed_polyglot",
        ),
    ),
    Dimension(
        id="modality",
        title="Input / output modality",
        layer="meta",
        description="Dominant media the agent must handle.",
        values=(
            "text_code",
            "tabular_excel",
            "image_vision",
            "logs_telemetry",
            "structured_json",
            "mixed_multimodal",
        ),
        matrix_axis=False,  # optional axis — enable when you have multimodal seeds
    ),
    Dimension(
        id="user_persona",
        title="Requester persona",
        layer="meta",
        description="Who is asking — affects tone, constraints, success criteria.",
        values=(
            "solo_dev",
            "startup_pm",
            "enterprise_eng",
            "data_analyst",
            "student_learner",
            "ops_sre",
        ),
        matrix_axis=False,
    ),
)

# ---------------------------------------------------------------------------
# GENERIC / operational dimensions (how the harness / agent loop runs)
# ---------------------------------------------------------------------------

GENERIC_DIMENSIONS: tuple[Dimension, ...] = (
    Dimension(
        id="agent_topology",
        title="Agent topology",
        layer="generic",
        description=(
            "Single-agent vs multi-agent. Current verification path is strongest "
            "as single-conversation with optional Agent subagents; full multi-agent "
            "spin is a known gap to expand."
        ),
        values=(
            "single_agent",
            "subagent_spawns",  # Plan/general-purpose/verification style
            "multi_agent_parallel",  # future
        ),
    ),
    Dimension(
        id="tool_profile",
        title="Tool use profile",
        layer="generic",
        description="Expected tool intensity and mix.",
        values=(
            "read_only",
            "edit_light",
            "edit_heavy",
            "shell_heavy",
            "browser_or_ui",
            "mixed_tools",
        ),
    ),
    Dimension(
        id="verification_mode",
        title="Verification mode",
        layer="generic",
        description="How success is checked after implementation.",
        values=(
            "none",
            "smoke_run",
            "unit_tests",
            "runtime_pass",  # harness RUNTIME_CHECK
            "human_review",
        ),
    ),
    Dimension(
        id="session_shape",
        title="Session shape",
        layer="generic",
        description="Turn structure of the example.",
        values=(
            "single_shot",
            "multi_turn_repair",
            "long_horizon",
        ),
    ),
    Dimension(
        id="repo_state",
        title="Starting repo state",
        layer="generic",
        description="What the agent inherits at turn 0.",
        values=(
            "empty_scratch",
            "partial_scaffold",
            "existing_buggy",
            "brownfield_large",
        ),
        matrix_axis=False,
    ),
)

# ---------------------------------------------------------------------------
# QUALITY bands — every example MUST have these
# ---------------------------------------------------------------------------

QUALITY_DIMENSIONS: tuple[Dimension, ...] = (
    Dimension(
        id="complexity",
        title="Complexity",
        layer="quality",
        description=(
            "How hard the task is for an agentic coder: scope, deps, ambiguity, "
            "verification depth. Bands: low | medium | hard."
        ),
        values=BANDS_LMH,
    ),
    Dimension(
        id="value",
        title="Training value",
        layer="quality",
        description=(
            "How valuable the example is for training an agentic model "
            "(signal density, transfer, rarity). Bands: low | medium | hard."
        ),
        values=BANDS_LMH,
    ),
)

ALL_DIMENSIONS: tuple[Dimension, ...] = (
    META_DIMENSIONS + GENERIC_DIMENSIONS + QUALITY_DIMENSIONS
)

DIMENSIONS_BY_ID: dict[str, Dimension] = {d.id: d for d in ALL_DIMENSIONS}


def matrix_axes(*, include_optional: bool = False) -> list[Dimension]:
    """Dimensions used in default cross-product planning."""
    out = []
    for d in ALL_DIMENSIONS:
        if d.matrix_axis or include_optional:
            out.append(d)
    return out


# Core axes → manageable thousands of combos (not the full cartesian bomb).
CORE_AXIS_IDS: tuple[str, ...] = (
    "task_family",
    "business_domain",
    "language_runtime",
    "complexity",
    "value",
)

# Default filters on core axes ≈ a few thousand cells (meaningful starter matrix).
STARTER_FILTERS: dict[str, set[str]] = {
    "task_family": {
        "coding_implement",
        "coding_debug",
        "coding_refactor",
        "analysis_reason",
        "data_visualization",
        "data_wrangling",
        "testing_qa",
        "spreadsheet_excel",
        "ml_inference_eval",
        "devops_ops",
    },
    "business_domain": {
        "ecommerce",
        "finance_fintech",
        "devops_platform",
        "gaming",
        "iot_automation",
        "media_cms",
        "productivity_collab",
        "social_comms",
        "data_analytics",
        "general_utilities",
    },
    "language_runtime": {
        "python",
        "typescript",
        "javascript",
        "cpp",
        "csharp",
        "excel_office",
        "mixed_polyglot",
    },
}


def core_matrix_axes() -> list[Dimension]:
    return [DIMENSIONS_BY_ID[i] for i in CORE_AXIS_IDS]


def taxonomy_export() -> dict[str, Any]:
    """JSON-serializable full taxonomy."""
    return {
        "bands": list(BANDS_LMH),
        "core_axis_ids": list(CORE_AXIS_IDS),
        "starter_filters": {k: sorted(v) for k, v in STARTER_FILTERS.items()},
        "layers": {
            "meta": [d.id for d in META_DIMENSIONS],
            "generic": [d.id for d in GENERIC_DIMENSIONS],
            "quality": [d.id for d in QUALITY_DIMENSIONS],
        },
        "dimensions": [
            {
                "id": d.id,
                "title": d.title,
                "layer": d.layer,
                "description": d.description,
                "values": list(d.values),
                "matrix_axis": d.matrix_axis,
            }
            for d in ALL_DIMENSIONS
        ],
    }
