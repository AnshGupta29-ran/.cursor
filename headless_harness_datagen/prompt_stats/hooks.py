"""Live hooks — call these whenever a forge or pipeline run completes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from prompt_stats.ledger import (
    append_record,
    prompt_fingerprint,
    record_id_for,
    upsert_merge,
    utc_now,
)
from prompt_stats.metrics import analyze_prompt_text, apply_effort_complexity


def _attach_dims_and_cost(record: dict[str, Any]) -> dict[str, Any]:
    """Stamp dimensions + USD/compute-unit estimate onto a ledger row."""
    try:
        from datagen_dims.classify import enrich_record
        from datagen_dims.costing import session_cost
    except ImportError:
        return record
    enrich_record(record)
    tin = record.get("input_tokens")
    if tin is None:
        tin = record.get("input_tokens_est")
    tout = record.get("output_tokens")
    if tout is None:
        tout = record.get("output_tokens_est")
    record["cost"] = session_cost(
        input_tokens=float(tin or 0),
        output_tokens=float(tout or 0),
    )
    return record


def record_raw_prompt(
    *,
    prompt: str,
    source: str,
    title: str | None = None,
    category: str | None = None,
    session_id: str | None = None,
    project: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record any free-form prompt (interactive Chakra, seed bank, etc.)."""
    text = (prompt or "").strip()
    fp = prompt_fingerprint(text)
    rid = record_id_for(source=source, key=session_id or title or fp, fingerprint=fp)
    metrics = analyze_prompt_text(text)
    record: dict[str, Any] = {
        "id": rid,
        "source": source,
        "kind": "prompt",
        "title": title or text[:80].replace("\n", " "),
        "seed": text if len(text) < 4000 else text[:4000],
        "prompt_fingerprint": fp,
        "category": category,
        "session_id": session_id,
        "project": project,
        "event_time": utc_now(),
        "metrics": metrics,
        "complexity_score": metrics["complexity_score"],
        "complexity_band": metrics["complexity_band"],
        "est_tokens": metrics["est_tokens"],
        "chars": metrics["chars"],
        "input_tokens_est": metrics["est_tokens"],
        "output_tokens_est": None,
        "total_tokens_est": metrics["est_tokens"],
    }
    if extra:
        # Allow callers to override event_time etc. without wiping core fields.
        for k, v in extra.items():
            if v is not None:
                record[k] = v
    _attach_dims_and_cost(record)
    upsert_merge(record)
    return record


def record_forge_event(
    *,
    seed: str,
    platform_prompt: str,
    category: str | None = None,
    classification: dict[str, Any] | None = None,
    template_used: str | None = None,
    out_dir: str | Path | None = None,
    run_id: str | None = None,
    composed_objective: str | None = None,
) -> dict[str, Any]:
    """Record a prompt-forge expansion (unique platform PRD)."""
    seed = (seed or "").strip()
    platform_prompt = platform_prompt or ""
    fp = prompt_fingerprint(platform_prompt or seed)
    key = run_id or str(out_dir or fp)
    rid = record_id_for(source="forge", key=key, fingerprint=fp)
    seed_m = analyze_prompt_text(seed)
    plat_m = analyze_prompt_text(platform_prompt)
    composed_m = (
        analyze_prompt_text(composed_objective) if composed_objective else None
    )
    record: dict[str, Any] = {
        "id": rid,
        "source": "forge",
        "kind": "forged_platform_prompt",
        "run_id": run_id,
        "title": _title_from_platform(platform_prompt) or seed[:80],
        "seed": seed,
        "category": category,
        "template_used": template_used,
        "classification": classification,
        "prompt_fingerprint": fp,
        "event_time": utc_now(),
        "paths": {"out_dir": str(out_dir) if out_dir else None},
        "seed_metrics": seed_m,
        "platform_metrics": plat_m,
        "composed_metrics": composed_m,
        "complexity_score": plat_m["complexity_score"],
        "complexity_band": plat_m["complexity_band"],
        "est_tokens": plat_m["est_tokens"],
        "chars": plat_m["chars"],
        "acceptance_checkboxes": plat_m["acceptance_checkboxes"],
        "headings": plat_m["headings"],
        # Estimated: seed≈input, generated PRD≈output
        "input_tokens_est": seed_m["est_tokens"],
        "output_tokens_est": plat_m["est_tokens"],
        "total_tokens_est": seed_m["est_tokens"] + plat_m["est_tokens"],
    }
    _attach_dims_and_cost(record)
    upsert_merge(record)
    return record


def record_pipeline_event(
    *,
    run_id: str,
    objective: str,
    repository_path: str | None = None,
    summary: dict[str, Any] | None = None,
    runtime_seconds: float | None = None,
    forge_meta: dict[str, Any] | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
) -> dict[str, Any]:
    """Record / merge a finished harness pipeline run."""
    summary = summary or {}
    objective = objective or summary.get("objective") or ""
    fp = prompt_fingerprint(objective)
    rid = record_id_for(source="pipeline", key=run_id, fingerprint=fp)
    obj_m = analyze_prompt_text(objective)
    life = summary.get("lifecycle_snapshot") or {}
    health = summary.get("health_snapshot") or {}

    record: dict[str, Any] = {
        "id": rid,
        "source": "pipeline",
        "kind": "harness_run",
        "run_id": run_id,
        "title": (forge_meta or {}).get("seed") or objective[:80].replace("\n", " "),
        "seed": (forge_meta or {}).get("seed"),
        "category": (forge_meta or {}).get("category"),
        "objective_fingerprint": fp,
        "event_time": summary.get("recorded_at") or utc_now(),
        "repository_path": repository_path or summary.get("repository_path"),
        "verdict": summary.get("verdict"),
        "completed": summary.get("completed"),
        "termination_reason": summary.get("termination_reason"),
        "turn_count": summary.get("turn_count"),
        "conversation_id": summary.get("conversation_id"),
        "runtime_seconds": runtime_seconds,
        "input_tokens": prompt_tokens,
        "output_tokens": completion_tokens,
        "total_tokens": (
            (prompt_tokens or 0) + (completion_tokens or 0)
            if prompt_tokens is not None or completion_tokens is not None
            else None
        ),
        "repair_iterations": life.get("repair_complete_count"),
        "verdict_fail_count": life.get("verdict_fail_count"),
        "authoritative_pass": life.get("authoritative_pass"),
        "health_stage": health.get("stage"),
        "objective_metrics": obj_m,
        "complexity_score": obj_m["complexity_score"],
        "complexity_band": obj_m["complexity_band"],
        "est_tokens": obj_m["est_tokens"],
        "chars": obj_m["chars"],
        "paths": {
            "summary": None,
        },
    }
    if forge_meta:
        record["forge"] = {
            "category": forge_meta.get("category"),
            "template_used": forge_meta.get("template_used"),
            "classification": forge_meta.get("classification"),
        }
        plat = analyze_prompt_text(forge_meta.get("platform_prompt") or "")
        seed_m = analyze_prompt_text(forge_meta.get("seed") or "")
        record["platform_metrics"] = plat
        record["complexity_score"] = plat["complexity_score"]
        record["complexity_band"] = plat["complexity_band"]
        # Forge: estimate input=seed tokens, output=platform prompt tokens
        if record.get("input_tokens") is None:
            record["input_tokens_est"] = seed_m["est_tokens"]
            record["output_tokens_est"] = plat["est_tokens"]
    # Blend in observed pipeline effort so short seeds aren't stuck on 'low'
    base_for_effort = {
        "complexity_score": record["complexity_score"],
        "complexity_band": record["complexity_band"],
    }
    effort = apply_effort_complexity(
        base_for_effort,
        runtime_seconds=runtime_seconds,
        tool_calls=int(summary.get("tool_calls") or life.get("tool_calls") or 0),
        assistant_messages=int(summary.get("turn_count") or 0),
    )
    record["complexity_score"] = effort["complexity_score"]
    record["complexity_band"] = effort["complexity_band"]
    record["complexity_score_prompt_only"] = effort.get("complexity_score_prompt_only")
    record["complexity_effort_bonus"] = effort.get("complexity_effort_bonus")
    if record.get("input_tokens") is None and record.get("input_tokens_est") is None:
        record["input_tokens_est"] = obj_m["est_tokens"]
    _attach_dims_and_cost(record)
    upsert_merge(record)
    return record


def build_session_records(
    stats: dict[str, Any], *, agent: str | None = None
) -> list[dict[str, Any]]:
    """Build session + model-slice ledger rows without writing."""
    agent_name = str(agent or stats.get("agent") or "chakra").strip().lower() or "chakra"
    if agent_name not in {"chakra", "pi"}:
        agent_name = "chakra"
    session_src = f"{agent_name}_session"
    model_src = f"{agent_name}_model"
    session_id = str(stats.get("session_id") or "")
    prompt = str(stats.get("seed") or "")
    fp = prompt_fingerprint(prompt)
    rid = record_id_for(
        source=session_src,
        key=session_id or fp,
        fingerprint=session_id or fp,
    )
    metrics = stats.get("metrics") or analyze_prompt_text(prompt)
    record: dict[str, Any] = {
        "id": rid,
        "source": session_src,
        "kind": f"{agent_name}_run",
        "agent": agent_name,
        "title": stats.get("title") or prompt[:80].replace("\n", " "),
        "seed": prompt if len(prompt) < 4000 else prompt[:4000],
        "prompt_fingerprint": fp,
        "session_id": session_id,
        "project": stats.get("project"),
        "model": stats.get("model"),
        "models_seen": stats.get("models_seen"),
        "event_time": stats.get("event_time") or utc_now(),
        "runtime_seconds": stats.get("runtime_seconds"),
        "tool_calls": stats.get("tool_calls"),
        "assistant_messages": stats.get("assistant_messages"),
        "metrics": metrics,
        "complexity_score": metrics.get("complexity_score"),
        "complexity_band": metrics.get("complexity_band"),
        "complexity_score_prompt_only": metrics.get("complexity_score_prompt_only"),
        "complexity_effort_bonus": metrics.get("complexity_effort_bonus"),
        "est_tokens": metrics.get("est_tokens"),
        "chars": metrics.get("chars"),
        "input_tokens": stats.get("input_tokens"),
        "output_tokens": stats.get("output_tokens"),
        "input_tokens_est": stats.get("input_tokens_est"),
        "output_tokens_est": stats.get("output_tokens_est"),
        "total_tokens_est": stats.get("total_tokens_est"),
        "tokens_are_estimated": stats.get("tokens_are_estimated", True),
        "paths": {"session": stats.get("session_path")},
        "schema_version": 1,
        "recorded_at": utc_now(),
    }
    if record["input_tokens"] is not None or record["output_tokens"] is not None:
        record["total_tokens"] = (record.get("input_tokens") or 0) + (
            record.get("output_tokens") or 0
        )
    blob = f"{record['title']} {record['seed']} {record.get('project') or ''}".lower()
    if "game" in blob or "task_games_" in blob:
        record["category"] = record.get("category") or "games"
    _attach_dims_and_cost(record)
    rows = [record]

    for sl in stats.get("model_breakdown") or []:
        model = str(sl.get("model") or "").strip()
        if not model:
            continue
        slice_id = record_id_for(
            source=model_src,
            key=f"{session_id}:{model}",
            fingerprint=f"{session_id}:{model}",
        )
        out_tok = sl.get("output_tokens")
        in_tok = sl.get("input_tokens")
        slice_rec: dict[str, Any] = {
            "id": slice_id,
            "source": model_src,
            "kind": "model_slice",
            "agent": agent_name,
            "title": f"{record['title']} · {model}"[:120],
            "seed": record["seed"],
            "prompt_fingerprint": fp,
            "session_id": session_id,
            "project": record.get("project"),
            "model": model,
            "category": record.get("category"),
            "event_time": sl.get("event_time") or record.get("event_time"),
            "runtime_seconds": sl.get("runtime_seconds"),
            "tool_calls": sl.get("tool_calls"),
            "assistant_messages": sl.get("assistant_messages"),
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "input_tokens_est": sl.get("input_tokens_est"),
            "output_tokens_est": sl.get("output_tokens_est"),
            "tokens_are_estimated": sl.get("tokens_are_estimated", True),
            "complexity_score": record.get("complexity_score"),
            "complexity_band": record.get("complexity_band"),
            "parent_session_id": session_id,
            "schema_version": 1,
            "recorded_at": utc_now(),
        }
        if in_tok is not None or out_tok is not None:
            slice_rec["total_tokens"] = (in_tok or 0) + (out_tok or 0)
        elif slice_rec.get("input_tokens_est") is not None or slice_rec.get(
            "output_tokens_est"
        ) is not None:
            slice_rec["total_tokens_est"] = (
                slice_rec.get("input_tokens_est") or 0
            ) + (slice_rec.get("output_tokens_est") or 0)
        _attach_dims_and_cost(slice_rec)
        rows.append(slice_rec)
    return rows


def record_session_event(
    stats: dict[str, Any], *, agent: str | None = None
) -> dict[str, Any]:
    """Upsert a Chakra/Pi CLI session with real runtime + token estimates."""
    rows = build_session_records(stats, agent=agent)
    for row in rows:
        upsert_merge(row)
    return rows[0]


def _title_from_platform(text: str) -> str | None:
    for line in (text or "").splitlines()[:8]:
        s = line.strip()
        if s.startswith("#"):
            return s.lstrip("#").strip()[:120]
    return None
