"""Datagen-focused views for the prompt_stats dashboard.

- Kimi3 token rollup (since a start date)
- Task dimensions catalog from the forged task bank + checkpoint status
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from prompt_stats.ledger import load_records

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "artifacts" / "datagen_task_bank" / "by_category"
CHECKPOINT = ROOT / "artifacts" / "datagen_pipeline" / "checkpoint.json"

# When the user said they started using kimi3 again for this pipeline wave
DEFAULT_KIMI_SINCE = os.getenv("DATAGEN_KIMI3_SINCE", "2026-08-13")


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def _since_dt(since: str | None = None) -> datetime:
    raw = (since or DEFAULT_KIMI_SINCE).strip()
    if len(raw) == 10:
        raw = raw + "T00:00:00+00:00"
    dt = _parse_dt(raw)
    if dt is None:
        dt = datetime(2026, 8, 13, tzinfo=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _is_kimi(model: str | None) -> bool:
    m = (model or "").lower()
    return "kimi" in m


def _tok_in(r: dict[str, Any]) -> int:
    if r.get("tokens_are_estimated") and r.get("input_tokens_est") is not None:
        return int(r["input_tokens_est"] or 0)
    if r.get("input_tokens") is not None:
        return int(r["input_tokens"] or 0)
    if r.get("input_tokens_est") is not None:
        return int(r["input_tokens_est"] or 0)
    return int(r.get("est_tokens") or 0)


def _tok_out(r: dict[str, Any]) -> int:
    if r.get("tokens_are_estimated") and r.get("output_tokens_est") is not None:
        return int(r["output_tokens_est"] or 0)
    if r.get("output_tokens") is not None:
        return int(r["output_tokens"] or 0)
    if r.get("output_tokens_est") is not None:
        return int(r["output_tokens_est"] or 0)
    return 0


def _tok_api_in(r: dict[str, Any]) -> int:
    if r.get("input_tokens_api") is not None:
        return int(r.get("input_tokens_api") or 0)
    if r.get("tokens_are_estimated"):
        return 0
    if r.get("input_tokens") is not None:
        return int(r.get("input_tokens") or 0)
    return 0


def _tok_api_out(r: dict[str, Any]) -> int:
    if r.get("output_tokens_api") is not None:
        return int(r.get("output_tokens_api") or 0)
    if r.get("tokens_are_estimated"):
        return 0
    if r.get("output_tokens") is not None:
        return int(r.get("output_tokens") or 0)
    return 0


def _tok_est_in(r: dict[str, Any]) -> int:
    if r.get("input_tokens_est") is not None:
        return int(r.get("input_tokens_est") or 0)
    if r.get("tokens_are_estimated"):
        return _tok_in(r)
    return 0


def _tok_est_out(r: dict[str, Any]) -> int:
    if r.get("output_tokens_est") is not None:
        return int(r.get("output_tokens_est") or 0)
    if r.get("tokens_are_estimated"):
        return _tok_out(r)
    return 0


def kimi3_token_report(since: str | None = None) -> dict[str, Any]:
    """Aggregate kimi* tokens since date — charged (exact) vs estimated separately."""
    start = _since_dt(since)
    rows = load_records()

    def in_window(r: dict[str, Any]) -> bool:
        when = _parse_dt(r.get("event_time") or r.get("recorded_at"))
        if when is None:
            return False
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        return when >= start

    kimi_rows = [r for r in rows if _is_kimi(r.get("model")) and in_window(r)]
    langfuse_rows = [
        r
        for r in kimi_rows
        if str(r.get("source") or "") in {"langfuse_usage", "langfuse_generation"}
    ]
    model_slices = [r for r in kimi_rows if str(r.get("source") or "").endswith("_model")]
    sessions = [
        r
        for r in kimi_rows
        if str(r.get("source") or "") in {"chakra_session", "pi_session", "pipeline"}
    ]
    autopilot = [r for r in kimi_rows if str(r.get("source") or "") == "autopilot_task"]

    # Prefer Langfuse billed rows when present; else model slices; else sessions.
    if langfuse_rows:
        token_pool = langfuse_rows
        using_model_slices = False
        pool_kind = "langfuse"
    elif model_slices:
        token_pool = model_slices
        using_model_slices = True
        pool_kind = "model_slices"
    elif sessions:
        token_pool = sessions
        using_model_slices = False
        pool_kind = "sessions"
    else:
        token_pool = autopilot
        using_model_slices = False
        pool_kind = "autopilot"

    charged_in = sum(_tok_api_in(r) for r in token_pool)
    charged_out = sum(_tok_api_out(r) for r in token_pool)
    est_in = sum(_tok_est_in(r) for r in token_pool)
    est_out = sum(_tok_est_out(r) for r in token_pool)
    exact_rows = sum(1 for r in token_pool if not r.get("tokens_are_estimated") and (_tok_api_in(r) + _tok_api_out(r)) > 0)

    by_day: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "charged_input": 0,
            "charged_output": 0,
            "charged_total": 0,
            "est_input": 0,
            "est_output": 0,
            "est_total": 0,
            "rows": 0,
        }
    )
    by_source: Counter[str] = Counter()

    for r in token_pool:
        when = _parse_dt(r.get("event_time") or r.get("recorded_at"))
        day = when.date().isoformat() if when else "?"
        cin, cout = _tok_api_in(r), _tok_api_out(r)
        ein, eout = _tok_est_in(r), _tok_est_out(r)
        by_day[day]["charged_input"] += cin
        by_day[day]["charged_output"] += cout
        by_day[day]["charged_total"] += cin + cout
        by_day[day]["est_input"] += ein
        by_day[day]["est_output"] += eout
        by_day[day]["est_total"] += ein + eout
        by_day[day]["rows"] += 1
        by_source[str(r.get("source") or "?")] += 1

    seen: set[str] = set()
    tasks: list[dict[str, Any]] = []

    def add_task(r: dict[str, Any]) -> None:
        rid = str(r.get("id") or "")
        key = rid or f"{r.get('source')}|{r.get('task_key')}|{r.get('event_time')}|{r.get('title')}"
        if key in seen:
            return
        seen.add(key)
        cin, cout = _tok_api_in(r), _tok_api_out(r)
        ein, eout = _tok_est_in(r), _tok_est_out(r)
        exact = (cin + cout) > 0 and not r.get("tokens_are_estimated")
        tasks.append(
            {
                "when": (r.get("event_time") or r.get("recorded_at") or "")[:19],
                "model": r.get("model"),
                "source": r.get("source"),
                "category": r.get("category"),
                "task_key": r.get("task_key"),
                "title": (r.get("title") or "")[:120],
                "charged_input": cin,
                "charged_output": cout,
                "charged_total": cin + cout,
                "est_input": ein,
                "est_output": eout,
                "est_total": ein + eout,
                # Primary display = charged when available
                "input_tokens": cin if exact else ein,
                "output_tokens": cout if exact else eout,
                "total_tokens": (cin + cout) if exact else (ein + eout),
                "runtime_seconds": r.get("runtime_seconds"),
                "tool_calls": r.get("tool_calls"),
                "estimated": not exact,
                "tokens_source": r.get("tokens_source") or ("provider" if exact else "estimate"),
                "verdict": r.get("verdict"),
            }
        )

    for r in langfuse_rows + autopilot + token_pool + kimi_rows:
        add_task(r)

    tasks.sort(key=lambda x: x.get("when") or "", reverse=True)
    days = [{"day": d, **by_day[d]} for d in sorted(by_day.keys())]

    return {
        "since": start.isoformat(),
        "model_filter": "kimi*",
        "row_count": len(token_pool),
        "window_rows": len(kimi_rows),
        "exact_rows": exact_rows,
        "using_model_slices": using_model_slices,
        "pool_kind": pool_kind,
        # Primary = charged/exact (what you pay when provider reports usage)
        "charged_input": charged_in,
        "charged_output": charged_out,
        "charged_total": charged_in + charged_out,
        "input_tokens": charged_in,
        "output_tokens": charged_out,
        "total_tokens": charged_in + charged_out,
        # Secondary = estimates (NOT a bill)
        "est_input": est_in,
        "est_output": est_out,
        "est_total": est_in + est_out,
        "provider_note": (
            "Charged totals use provider/Langfuse usage only. "
            "Estimates are char-based guesses and are NOT your bill. "
            "If charged=0, the kimi proxy is not returning usage in transcripts — check Langfuse/TensorStudio billing."
        ),
        "by_day": days,
        "by_source": dict(by_source),
        "tasks": tasks[:500],
    }


def _load_checkpoint() -> dict[str, Any]:
    if not CHECKPOINT.is_file():
        return {}
    try:
        return json.loads(CHECKPOINT.read_text(encoding="utf-8")).get("tasks") or {}
    except json.JSONDecodeError:
        return {}


def dimensions_catalog() -> dict[str, Any]:
    """All forged tasks with dimension locks + checkpoint status."""
    ckpt = _load_checkpoint()
    items: list[dict[str, Any]] = []
    lang_counts: Counter[str] = Counter()
    ui_counts: Counter[str] = Counter()
    cx_counts: Counter[str] = Counter()
    persist_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()

    if not BANK.is_dir():
        return {"items": [], "totals": {}}

    for cat_dir in sorted(p for p in BANK.iterdir() if p.is_dir()):
        for seed_path in sorted(cat_dir.glob("*.json")):
            try:
                seed = json.loads(seed_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            idx = int(seed.get("index") or 0)
            hint = dict(seed.get("dimensions_hint") or {})
            task_key = f"{cat_dir.name}:{idx:02d}"
            st = (ckpt.get(task_key) or {}).get("status") or "not_started"
            lang = str(hint.get("language_runtime") or "?")
            ui = str(hint.get("ui_surface") or "?")
            cx = str(hint.get("complexity") or "?")
            persist = str(hint.get("persistence") or "?")
            lang_counts[lang] += 1
            ui_counts[ui] += 1
            cx_counts[cx] += 1
            persist_counts[persist] += 1
            status_counts[st] += 1
            forged = list((cat_dir / "forged").glob(f"{idx:02d}_*/platform_prompt.md"))
            items.append(
                {
                    "task_key": task_key,
                    "category": cat_dir.name,
                    "index": idx,
                    "title": seed.get("title") or seed_path.stem,
                    "workdir": seed.get("workdir") or f"task_{cat_dir.name}_{idx:02d}",
                    "status": st,
                    "dimensions": {
                        "language_runtime": lang,
                        "ui_surface": ui,
                        "persistence": persist,
                        "complexity": cx,
                        "verification_mode": hint.get("verification_mode"),
                        "testing_depth": hint.get("testing_depth"),
                        "user_persona": hint.get("user_persona"),
                        "novelty_hook": hint.get("novelty_hook"),
                        "delivery": hint.get("delivery"),
                        "artifact_type": hint.get("artifact_type"),
                        "agent_topology": hint.get("agent_topology"),
                        "session_shape": hint.get("session_shape"),
                        "tool_profile": hint.get("tool_profile"),
                        "repo_state": hint.get("repo_state"),
                        "value": hint.get("value"),
                        "modality": hint.get("modality"),
                        "business_domain": hint.get("business_domain"),
                        "task_family": hint.get("task_family"),
                    },
                    "platform_prompt": str(forged[0]) if forged else None,
                }
            )

    items.sort(key=lambda x: (x["category"], x["index"]))
    return {
        "count": len(items),
        "status_counts": dict(status_counts),
        "language_counts": dict(lang_counts.most_common()),
        "ui_counts": dict(ui_counts.most_common()),
        "complexity_counts": dict(cx_counts.most_common()),
        "persistence_counts": dict(persist_counts.most_common()),
        "items": items,
    }


def record_autopilot_task(
    *,
    task_key: str,
    title: str,
    category: str,
    model: str,
    workdir: str,
    platform_prompt: str,
    dimensions: dict[str, Any] | None,
    input_tokens: int | None,
    output_tokens: int | None,
    runtime_seconds: float | None,
    tool_calls: int | None,
    status: str,
    run_id: str | None = None,
) -> None:
    """Append/upsert one autopilot task into the prompt_stats ledger."""
    from prompt_stats.ledger import record_id_for, prompt_fingerprint, upsert_merge, utc_now
    from prompt_stats.metrics import analyze_prompt_text

    try:
        text = Path(platform_prompt).read_text(encoding="utf-8") if platform_prompt else title
    except OSError:
        text = title
    metrics = analyze_prompt_text(text[:20000])
    tin = int(input_tokens or 0)
    tout = int(output_tokens or 0)
    fp = prompt_fingerprint(f"{task_key}|{run_id or ''}|{text[:500]}")
    rid = record_id_for(source="autopilot_task", key=f"{task_key}|{run_id or status}", fingerprint=fp)
    upsert_merge(
        {
            "id": rid,
            "source": "autopilot_task",
            "kind": "autopilot_run",
            "agent": "chakra",
            "title": f"{task_key}: {title}"[:200],
            "seed": title,
            "prompt_fingerprint": fp,
            "category": category,
            "task_key": task_key,
            "workdir": workdir,
            "model": model,
            "models_seen": [model] if model else [],
            "event_time": utc_now(),
            "runtime_seconds": runtime_seconds,
            "tool_calls": tool_calls,
            "input_tokens": tin or None,
            "output_tokens": tout or None,
            "total_tokens": (tin + tout) or None,
            "tokens_are_estimated": tin == 0 and tout == 0,
            "verdict": status,
            "dimensions": dimensions or {},
            "complexity_score": metrics.get("complexity_score"),
            "complexity_band": metrics.get("complexity_band"),
            "est_tokens": metrics.get("est_tokens"),
            "run_id": run_id,
        }
    )
