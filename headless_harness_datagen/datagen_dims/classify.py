"""Heuristic assignment of dimension values to a prompt / session record."""

from __future__ import annotations

import re
from typing import Any

from datagen_dims.taxonomy import BANDS_LMH


def _score_band(score: float) -> str:
    """Map 0–100 complexity-like score → low|medium|hard."""
    if score < 30:
        return "low"
    if score < 65:
        return "medium"
    return "hard"


def assign_dimensions(
    *,
    text: str = "",
    title: str = "",
    category: str | None = None,
    complexity_score: float | None = None,
    runtime_seconds: float | None = None,
    tool_calls: int | None = None,
    source: str | None = None,
) -> dict[str, str]:
    """Return a full dimension dict; always includes complexity + value."""
    blob = f"{title}\n{text}\n{category or ''}".lower()

    dims: dict[str, str] = {
        "task_family": _task_family(blob),
        "business_domain": _business_domain(blob, category),
        "artifact_type": _artifact_type(blob),
        "language_runtime": _language(blob),
        "modality": _modality(blob),
        "user_persona": "solo_dev",
        "agent_topology": _topology(source, tool_calls),
        "tool_profile": _tool_profile(tool_calls, runtime_seconds),
        "verification_mode": _verification(source, blob),
        "session_shape": _session_shape(runtime_seconds, tool_calls),
        "repo_state": "empty_scratch",
    }

    # Complexity: prefer measured score + effort; else heuristic from text length
    if complexity_score is not None:
        dims["complexity"] = _score_band(float(complexity_score))
    else:
        dims["complexity"] = _complexity_from_text(blob, text)

    # Value: higher when domain-specific + hard + long successful effort
    dims["value"] = _value_band(dims, runtime_seconds, tool_calls, blob)
    return dims


def _task_family(blob: str) -> str:
    rules = [
        ("spreadsheet_excel", ("excel", "spreadsheet", "workbook", "xlsx")),
        ("data_visualization", ("chart", "dashboard", "visualiz", "plotly", "d3")),
        ("data_wrangling", ("etl", "pandas", "csv", "data pipeline", "wrangl")),
        ("ml_inference_eval", ("model", "pytorch", "tensorflow", "classifier", "nlp")),
        ("coding_debug", ("debug", "fix bug", "traceback", "regression")),
        ("coding_refactor", ("refactor", "migrate", "cleanup")),
        ("coding_review", ("code review", "pr review")),
        ("testing_qa", ("unit test", "pytest", "test suite", "qa")),
        ("documentation", ("readme", "docs only", "documentation")),
        ("devops_ops", ("docker", "kubernetes", "ci/cd", "terraform", "deploy")),
        ("security_audit", ("security", "authz", "owasp", "encrypt")),
        ("planning_decompose", ("write a plan", "decompose", "architecture design")),
        ("analysis_reason", ("analy", "reason through", "investigate")),
        ("research_synthesize", ("research", "survey", "literature")),
    ]
    for label, keys in rules:
        if any(k in blob for k in keys):
            return label
    return "coding_implement"


def _business_domain(blob: str, category: str | None) -> str:
    cat_map = {
        "ecommerce": "ecommerce",
        "finance_productivity": "finance_fintech",
        "games": "gaming",
        "iot_automation": "iot_automation",
        "cms_content": "media_cms",
        "security_privacy": "security_privacy",
        "collaborative_realtime": "productivity_collab",
        "devops_infra": "devops_platform",
        "monitoring_ops": "devops_platform",
        "ai_ml": "data_analytics",
        "storage_files": "general_utilities",
        "distributed_systems": "devops_platform",
    }
    if category and category in cat_map:
        return cat_map[category]
    rules = [
        ("ecommerce", ("ecom", "commerce", "shop", "cart", "inventory")),
        ("finance_fintech", ("finance", "trading", "invoice", "payment", "bank")),
        ("healthcare", ("health", "patient", "clinic", "medical")),
        ("education", ("school", "course", "student", "lms")),
        ("gaming", ("game", "unity", "tower defense", "player")),
        ("iot_automation", ("iot", "smart home", "sensor", "thermostat")),
        ("media_cms", ("cms", "blog", "content", "publisher")),
        ("security_privacy", ("password vault", "encryption", "oauth")),
        ("productivity_collab", ("whiteboard", "collab", "taskflow", "habit")),
        ("social_comms", ("social", "chat", "messaging", "feed")),
        ("logistics_ops", ("logistics", "shipping", "warehouse")),
        ("data_analytics", ("analytics", "classification", "ml ")),
    ]
    for label, keys in rules:
        if any(k in blob for k in keys):
            return label
    return "general_utilities"


def _artifact_type(blob: str) -> str:
    rules = [
        ("spreadsheet_workbook", ("excel", "xlsx", "workbook")),
        ("game_prototype", ("game", "unity", "pygame")),
        ("notebook_analysis", ("jupyter", "notebook")),
        ("cli_tool", ("cli", "command-line", "argparse")),
        ("library_sdk", ("sdk", "library package")),
        ("infra_as_code", ("terraform", "helm", "pulumi")),
        ("data_pipeline", ("pipeline", "etl", "airflow")),
        ("desktop_app", ("desktop", "pyside", "electron")),
        ("backend_api", ("fastapi", "rest api", "express", "grpc")),
        ("frontend_spa", ("react", "vue", "vite", "spa")),
        ("test_suite", ("test suite only",)),
        ("docs_spec", ("documentation only", "prd only")),
        ("web_fullstack", ("full-stack", "fullstack", "full stack")),
    ]
    for label, keys in rules:
        if any(k in blob for k in keys):
            return label
    if "api" in blob:
        return "backend_api"
    return "web_fullstack"


def _language(blob: str) -> str:
    rules = [
        ("excel_office", ("excel", "xlsx", "vba")),
        ("csharp", ("c#", "csharp", "unity", ".net")),
        ("cpp", ("c++", "cpp")),
        ("rust", ("rust", "cargo")),
        ("go", ("golang", " go ")),
        ("java", ("java", "spring")),
        ("typescript", ("typescript", "tsx")),
        ("javascript", ("javascript", "node.js", "express")),
        ("python", ("python", "fastapi", "django", "flask", "pytest")),
        ("sql", ("postgresql", "sqlite", "prisma", "sql ")),
        ("bash_shell", ("bash", "powershell")),
        ("html_css", ("html", "css only")),
    ]
    hits = [lab for lab, keys in rules if any(k in blob for k in keys)]
    if len(hits) >= 2:
        return "mixed_polyglot"
    return hits[0] if hits else "python"


def _modality(blob: str) -> str:
    if any(k in blob for k in ("image", "vision", "opencv", "pytorch")):
        return "image_vision"
    if any(k in blob for k in ("excel", "csv", "tabular")):
        return "tabular_excel"
    if any(k in blob for k in ("log ", "telemetry", "metrics")):
        return "logs_telemetry"
    return "text_code"


def _topology(source: str | None, tool_calls: int | None) -> str:
    if source in {"pipeline", "forge"}:
        return "subagent_spawns"
    return "single_agent"


def _tool_profile(tool_calls: int | None, runtime: float | None) -> str:
    tc = tool_calls or 0
    if tc == 0:
        return "read_only"
    if tc < 15:
        return "edit_light"
    if tc < 60:
        return "edit_heavy"
    return "shell_heavy" if (runtime or 0) > 1800 else "mixed_tools"


def _verification(source: str | None, blob: str) -> str:
    if source == "pipeline":
        return "runtime_pass"
    if "pytest" in blob or "unit test" in blob:
        return "unit_tests"
    if "smoke" in blob:
        return "smoke_run"
    return "smoke_run"


def _session_shape(runtime: float | None, tool_calls: int | None) -> str:
    rt = runtime or 0
    tc = tool_calls or 0
    if rt > 2400 or tc > 80:
        return "long_horizon"
    if rt > 300 or tc > 20:
        return "multi_turn_repair"
    return "single_shot"


def _complexity_from_text(blob: str, text: str) -> str:
    n = len(text or "")
    feature_hits = len(
        re.findall(
            r"auth|dashboard|realtime|websocket|payment|inventory|test|api|docker",
            blob,
        )
    )
    if n > 4000 or feature_hits >= 6:
        return "hard"
    if n > 800 or feature_hits >= 3:
        return "medium"
    return "low"


def _value_band(
    dims: dict[str, str],
    runtime: float | None,
    tool_calls: int | None,
    blob: str,
) -> str:
    """Hard complexity + distinctive domain + real effort → higher training value."""
    score = 0
    if dims.get("complexity") == "hard":
        score += 2
    elif dims.get("complexity") == "medium":
        score += 1
    if dims.get("business_domain") not in {"general_utilities"}:
        score += 1
    if (runtime or 0) > 1800 or (tool_calls or 0) > 40:
        score += 1
    if any(k in blob for k in ("acceptance", "unique", "domain")):
        score += 1
    if score >= 4:
        return "hard"
    if score >= 2:
        return "medium"
    return "low"


def enrich_record(record: dict[str, Any]) -> dict[str, Any]:
    """Attach dimensions (+ keep existing if already set)."""
    existing = record.get("dimensions") if isinstance(record.get("dimensions"), dict) else {}
    assigned = assign_dimensions(
        text=str(record.get("seed") or record.get("objective") or ""),
        title=str(record.get("title") or ""),
        category=record.get("category"),
        complexity_score=(
            float(record["complexity_score"])
            if record.get("complexity_score") is not None
            else None
        ),
        runtime_seconds=(
            float(record["runtime_seconds"])
            if isinstance(record.get("runtime_seconds"), (int, float))
            else None
        ),
        tool_calls=(
            int(record["tool_calls"])
            if isinstance(record.get("tool_calls"), int)
            else None
        ),
        source=record.get("source"),
    )
    record["dimensions"] = {**assigned, **existing}
    # Mirror quality bands at top level for easy filtering
    record["complexity_band_lmh"] = record["dimensions"]["complexity"]
    record["value_band"] = record["dimensions"]["value"]
    return record
