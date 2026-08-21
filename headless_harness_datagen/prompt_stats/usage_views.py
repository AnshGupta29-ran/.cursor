"""Clean usage analytics for the prompt_stats dashboard.

Rules:
- Charged/exact = provider or Langfuse usage only (input_tokens_api / non-estimated input_tokens).
- Estimates are NEVER shown as charged.
- Token KPIs exclude forge/task_bank/readme noise.
- Sessions are attributed to task_key via workdir / project path when possible.
"""

from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from prompt_stats.ledger import load_records

DEFAULT_SINCE = os.getenv("DATAGEN_KIMI3_SINCE", "2026-08-13")
CHECKPOINT = (
    Path(__file__).resolve().parents[1]
    / "artifacts"
    / "datagen_pipeline"
    / "checkpoint.json"
)

USAGE_SOURCES = frozenset(
    {
        "chakra_session",
        "chakra_model",
        "pi_session",
        "pi_model",
        "autopilot_task",
        "langfuse_usage",
        "langfuse_generation",
        "pipeline",
    }
)


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def _since_dt(since: str | None) -> datetime | None:
    if not since:
        return None
    raw = since.strip()
    if len(raw) == 10:
        raw = raw + "T00:00:00+00:00"
    dt = _parse_dt(raw)
    if dt and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _agent(r: dict[str, Any]) -> str:
    if r.get("agent") in {"chakra", "pi"}:
        return str(r["agent"])
    src = str(r.get("source") or "")
    if src.startswith("pi_"):
        return "pi"
    if src.startswith("chakra_") or src in {
        "pipeline",
        "autopilot_task",
        "langfuse_usage",
        "langfuse_generation",
    }:
        return "chakra"
    return "other"


def _is_usage_row(r: dict[str, Any]) -> bool:
    return str(r.get("source") or "") in USAGE_SOURCES


def charged_in(r: dict[str, Any]) -> int:
    if r.get("input_tokens_api") is not None:
        return max(0, int(r.get("input_tokens_api") or 0))
    if r.get("tokens_are_estimated"):
        return 0
    if r.get("input_tokens") is not None:
        return max(0, int(r.get("input_tokens") or 0))
    return 0


def charged_out(r: dict[str, Any]) -> int:
    if r.get("output_tokens_api") is not None:
        return max(0, int(r.get("output_tokens_api") or 0))
    if r.get("tokens_are_estimated"):
        return 0
    if r.get("output_tokens") is not None:
        return max(0, int(r.get("output_tokens") or 0))
    return 0


def est_in(r: dict[str, Any]) -> int:
    if r.get("input_tokens_est") is not None:
        return max(0, int(r.get("input_tokens_est") or 0))
    if r.get("tokens_are_estimated") and r.get("input_tokens") is not None:
        return max(0, int(r.get("input_tokens") or 0))
    if r.get("est_tokens") is not None and r.get("tokens_are_estimated"):
        return max(0, int(r.get("est_tokens") or 0))
    return 0


def est_out(r: dict[str, Any]) -> int:
    if r.get("output_tokens_est") is not None:
        return max(0, int(r.get("output_tokens_est") or 0))
    if r.get("tokens_are_estimated") and r.get("output_tokens") is not None:
        return max(0, int(r.get("output_tokens") or 0))
    return 0


def has_exact(r: dict[str, Any]) -> bool:
    return (charged_in(r) + charged_out(r)) > 0 and not r.get("tokens_are_estimated")


_TASK_RE = re.compile(
    r"(?:^|[^\w])(?:task[_-])?([a-z0-9]+(?:_[a-z0-9]+)*)[_-](\d{2})(?:[^\d]|$)",
    re.I,
)
_TASK_DASH_RE = re.compile(
    r"task[_-]([a-z0-9]+(?:[_-][a-z0-9]+)*)[_-](\d{2})",
    re.I,
)
_CAT_RE = re.compile(r"\b([a-z0-9_]+):(\d{2})\b", re.I)

# known categories for dash-encoded chakra project paths
_KNOWN_CATS = (
    "ai_ml",
    "games",
    "cms_content",
    "collaborative_realtime",
    "devops_infra",
    "distributed_systems",
    "ecommerce",
    "finance_productivity",
    "generic_fullstack",
    "iot_automation",
    "monitoring_ops",
    "security_privacy",
    "storage_files",
)


def infer_task_key(r: dict[str, Any]) -> str | None:
    if r.get("task_key"):
        return str(r["task_key"])
    hay = " ".join(
        str(x or "")
        for x in (
            r.get("workdir"),
            r.get("project"),
            r.get("title"),
            r.get("seed"),
            (r.get("paths") or {}).get("session") if isinstance(r.get("paths"), dict) else "",
        )
    )
    m = _CAT_RE.search(hay)
    if m and m.group(1) in _KNOWN_CATS:
        return f"{m.group(1)}:{m.group(2)}"

    # Normalize Windows / Chakra project encodings: \ → /, -- → /, _ stays
    norm = hay.replace("\\", "/").replace("--", "/")
    # task_cms_content_04 or task-cms-content-04
    m = _TASK_DASH_RE.search(norm.replace("/", "-"))
    if m:
        cat = m.group(1).replace("-", "_")
        if cat in _KNOWN_CATS:
            return f"{cat}:{m.group(2)}"

    for cat in _KNOWN_CATS:
        dash = cat.replace("_", "-")
        for pattern in (
            rf"task[_-]{re.escape(cat)}[_-](\d{{2}})",
            rf"task[_-]{re.escape(dash)}[_-](\d{{2}})",
            rf"/{re.escape(cat)}[_-](\d{{2}})\b",
            rf"experiments[_/-]task[_-]{re.escape(dash)}[_-](\d{{2}})",
            rf"experiments[_/-]task[_-]{re.escape(cat)}[_-](\d{{2}})",
        ):
            mm = re.search(pattern, norm, re.I)
            if mm:
                return f"{cat}:{mm.group(1)}"
    return None


def _token_pool(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    """Pick non-overlapping pool for Σ (prefer exact sources)."""
    lf = [r for r in rows if str(r.get("source") or "").startswith("langfuse")]
    if any(has_exact(r) for r in lf):
        return [r for r in lf if has_exact(r)], "langfuse"
    models = [r for r in rows if str(r.get("source") or "").endswith("_model")]
    exact_models = [r for r in models if has_exact(r)]
    if exact_models:
        return exact_models, "model_slices_exact"
    sessions = [
        r
        for r in rows
        if str(r.get("source") or "")
        in {"chakra_session", "pi_session", "pipeline", "autopilot_task"}
    ]
    exact_sess = [r for r in sessions if has_exact(r)]
    if exact_sess:
        return exact_sess, "sessions_exact"
    # No exact usage — return empty for charged; estimates use sessions separately
    return [], "none_exact"


def _estimate_pool(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    models = [r for r in rows if str(r.get("source") or "").endswith("_model")]
    if models:
        return models
    return [
        r
        for r in rows
        if str(r.get("source") or "")
        in {"chakra_session", "pi_session", "pipeline", "autopilot_task"}
    ]


def usage_report(
    *,
    since: str | None = None,
    agent: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    start = _since_dt(since)
    rows = [r for r in load_records() if _is_usage_row(r)]

    filtered: list[dict[str, Any]] = []
    for r in rows:
        when = _parse_dt(r.get("event_time") or r.get("recorded_at"))
        if start and when:
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            if when < start:
                continue
        elif start and not when:
            continue
        if agent and _agent(r) != agent:
            continue
        if model and str(r.get("model") or "") != model:
            continue
        filtered.append(r)

    charged_pool, pool_kind = _token_pool(filtered)
    est_pool = _estimate_pool(filtered)

    cin = sum(charged_in(r) for r in charged_pool)
    cout = sum(charged_out(r) for r in charged_pool)
    ein = sum(est_in(r) for r in est_pool)
    eout = sum(est_out(r) for r in est_pool)

    # Time: sessions/autopilot only (not model slices — avoid double count)
    time_rows = [
        r
        for r in filtered
        if str(r.get("source") or "")
        in {"chakra_session", "pi_session", "autopilot_task", "pipeline"}
        and isinstance(r.get("runtime_seconds"), (int, float))
    ]
    total_time = sum(float(r["runtime_seconds"]) for r in time_rows)

    by_agent: dict[str, dict[str, Any]] = {}
    by_model: dict[str, dict[str, Any]] = {}

    def bump(bucket: dict[str, dict[str, Any]], key: str, r: dict[str, Any], *, for_charge: bool, for_est: bool, for_time: bool) -> None:
        g = bucket.setdefault(
            key,
            {
                "key": key,
                "sessions": 0,
                "charged_input": 0,
                "charged_output": 0,
                "charged_total": 0,
                "est_input": 0,
                "est_output": 0,
                "est_total": 0,
                "runtime_seconds": 0.0,
                "exact_rows": 0,
            },
        )
        src = str(r.get("source") or "")
        if for_time and (src.endswith("_session") or src == "autopilot_task" or src == "pipeline"):
            g["sessions"] += 1
            if isinstance(r.get("runtime_seconds"), (int, float)):
                g["runtime_seconds"] += float(r["runtime_seconds"])
        if for_charge:
            a, b = charged_in(r), charged_out(r)
            g["charged_input"] += a
            g["charged_output"] += b
            g["charged_total"] += a + b
            if a + b > 0:
                g["exact_rows"] += 1
        if for_est:
            a, b = est_in(r), est_out(r)
            g["est_input"] += a
            g["est_output"] += b
            g["est_total"] += a + b

    charge_set = {id(r) for r in charged_pool}
    est_set = {id(r) for r in est_pool}
    for r in filtered:
        a = _agent(r)
        m = str(r.get("model") or "unknown")
        bump(by_agent, a, r, for_charge=id(r) in charge_set, for_est=id(r) in est_set, for_time=True)
        bump(
            by_model,
            f"{a}::{m}",
            r,
            for_charge=id(r) in charge_set,
            for_est=id(r) in est_set,
            for_time=True,
        )

    # Per-task rollup
    by_task: dict[str, dict[str, Any]] = {}
    for r in filtered:
        tk = infer_task_key(r)
        if not tk:
            continue
        g = by_task.setdefault(
            tk,
            {
                "task_key": tk,
                "title": None,
                "agent": _agent(r),
                "model": r.get("model"),
                "charged_input": 0,
                "charged_output": 0,
                "charged_total": 0,
                "est_input": 0,
                "est_output": 0,
                "est_total": 0,
                "runtime_seconds": 0.0,
                "runs": 0,
                "sources": Counter(),
                "last_when": "",
            },
        )
        src = str(r.get("source") or "")
        # Prefer session/autopilot for time; model/langfuse for tokens
        if src.endswith("_model") or src.startswith("langfuse") or src == "autopilot_task":
            if has_exact(r) or src.startswith("langfuse"):
                a, b = charged_in(r), charged_out(r)
                g["charged_input"] += a
                g["charged_output"] += b
                g["charged_total"] += a + b
            a, b = est_in(r), est_out(r)
            g["est_input"] += a
            g["est_output"] += b
            g["est_total"] += a + b
        if src.endswith("_session") or src == "autopilot_task":
            g["runs"] += 1
            if isinstance(r.get("runtime_seconds"), (int, float)):
                # take max per overlapping slices roughly — sum sessions
                g["runtime_seconds"] += float(r["runtime_seconds"])
            if not g["title"]:
                g["title"] = (r.get("title") or "")[:120]
            if r.get("model"):
                g["model"] = r.get("model")
        g["sources"][src] += 1
        when = (r.get("event_time") or r.get("recorded_at") or "")[:19]
        if when > (g["last_when"] or ""):
            g["last_when"] = when

    # Enrich titles from checkpoint
    try:
        import json

        if CHECKPOINT.is_file():
            ckpt = json.loads(CHECKPOINT.read_text(encoding="utf-8")).get("tasks") or {}
            for tk, g in by_task.items():
                row = ckpt.get(tk) or {}
                if row.get("workdir") and not g.get("title"):
                    g["title"] = row.get("workdir")
                g["status"] = row.get("status")
    except Exception:
        pass

    tasks = []
    for g in by_task.values():
        tasks.append(
            {
                **{k: v for k, v in g.items() if k != "sources"},
                "sources": dict(g["sources"]),
            }
        )
    tasks.sort(key=lambda x: x.get("last_when") or "", reverse=True)

    # Row-level detail for table (sessions + autopilot + langfuse + exact models)
    detail: list[dict[str, Any]] = []
    for r in filtered:
        src = str(r.get("source") or "")
        if src.endswith("_model") and not has_exact(r):
            # skip pure estimate model slices in detail to reduce noise/dupe
            continue
        if src not in USAGE_SOURCES:
            continue
        exact = has_exact(r)
        detail.append(
            {
                "when": (r.get("event_time") or r.get("recorded_at") or "")[:19],
                "agent": _agent(r),
                "model": r.get("model") or "—",
                "source": src,
                "task_key": infer_task_key(r) or "—",
                "title": (r.get("title") or "")[:100],
                "charged_input": charged_in(r),
                "charged_output": charged_out(r),
                "charged_total": charged_in(r) + charged_out(r),
                "est_input": est_in(r),
                "est_output": est_out(r),
                "est_total": est_in(r) + est_out(r),
                "runtime_seconds": r.get("runtime_seconds"),
                "tool_calls": r.get("tool_calls"),
                "exact": exact,
                "tokens_source": r.get("tokens_source")
                or ("provider" if exact else "estimate"),
            }
        )
    detail.sort(key=lambda x: x.get("when") or "", reverse=True)

    by_day: dict[str, dict[str, int]] = defaultdict(
        lambda: {"charged_total": 0, "est_total": 0, "runtime_seconds": 0, "rows": 0}
    )
    for r in charged_pool:
        when = _parse_dt(r.get("event_time") or r.get("recorded_at"))
        day = when.date().isoformat() if when else "?"
        by_day[day]["charged_total"] += charged_in(r) + charged_out(r)
        by_day[day]["rows"] += 1
    for r in est_pool:
        when = _parse_dt(r.get("event_time") or r.get("recorded_at"))
        day = when.date().isoformat() if when else "?"
        by_day[day]["est_total"] += est_in(r) + est_out(r)
    for r in time_rows:
        when = _parse_dt(r.get("event_time") or r.get("recorded_at"))
        day = when.date().isoformat() if when else "?"
        by_day[day]["runtime_seconds"] += int(float(r["runtime_seconds"]))

    return {
        "since": start.isoformat() if start else None,
        "pool_kind": pool_kind,
        "usage_rows": len(filtered),
        "charged_input": cin,
        "charged_output": cout,
        "charged_total": cin + cout,
        "est_input": ein,
        "est_output": eout,
        "est_total": ein + eout,
        "runtime_seconds": round(total_time, 1),
        "exact_rows": sum(1 for r in charged_pool if has_exact(r)),
        "note": (
            "Charged = provider/Langfuse usage only. "
            "Estimate = char-based guess (often huge; NOT a bill). "
            "If charged is 0, the model proxy did not return usage blobs."
        ),
        "by_agent": sorted(by_agent.values(), key=lambda x: -x["runtime_seconds"]),
        "by_model": sorted(by_model.values(), key=lambda x: -x["charged_total"] or -x["est_total"]),
        "by_task": tasks[:300],
        "by_day": [{"day": d, **by_day[d]} for d in sorted(by_day.keys())],
        "rows": detail[:400],
        "models": sorted(
            {
                str(r.get("model"))
                for r in filtered
                if isinstance(r.get("model"), str) and r.get("model").strip()
            }
        ),
        "agents": sorted({_agent(r) for r in filtered}),
    }
