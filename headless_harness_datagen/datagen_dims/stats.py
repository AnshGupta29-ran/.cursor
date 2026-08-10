"""Aggregate token / cost stats from the prompt_stats ledger by dimension."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from datagen_dims.classify import enrich_record
from datagen_dims.costing import pricing_from_env, session_cost
from prompt_stats.ledger import load_records


def _tokens_of(r: dict[str, Any]) -> tuple[float, float]:
    tin = r.get("input_tokens")
    if tin is None:
        tin = r.get("input_tokens_est")
    tout = r.get("output_tokens")
    if tout is None:
        tout = r.get("output_tokens_est")
    if tin is None and r.get("est_tokens") is not None:
        tin = r.get("est_tokens")
    return float(tin or 0), float(tout or 0)


def ledger_with_dimensions(records: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    rows = []
    for r in records if records is not None else load_records():
        rows.append(enrich_record(dict(r)))
    return rows


def category_token_averages(
    records: list[dict[str, Any]] | None = None,
    *,
    group_by: str = "business_domain",
) -> dict[str, Any]:
    """Average in/out/total tokens (+ $) per dimension value."""
    pricing = pricing_from_env()
    rows = ledger_with_dimensions(records)
    buckets: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for r in rows:
        dims = r.get("dimensions") or {}
        key = str(dims.get(group_by) or r.get("category") or "unknown")
        buckets[key].append(_tokens_of(r))

    out: dict[str, Any] = {"group_by": group_by, "groups": {}, "pricing": {
        "model": pricing.model,
        "input_usd_per_m": pricing.input_usd_per_m,
        "output_usd_per_m": pricing.output_usd_per_m,
    }}
    for key, pairs in sorted(buckets.items()):
        n = len(pairs)
        sin = sum(a for a, _ in pairs)
        sout = sum(b for _, b in pairs)
        avg_in = sin / n if n else 0
        avg_out = sout / n if n else 0
        cost = session_cost(
            input_tokens=avg_in, output_tokens=avg_out, pricing=pricing
        )
        out["groups"][key] = {
            "n_sessions": n,
            "avg_input_tokens": round(avg_in, 1),
            "avg_output_tokens": round(avg_out, 1),
            "avg_total_tokens": round(avg_in + avg_out, 1),
            "avg_usd": cost["usd"],
            "avg_compute_units": cost["compute_units"],
            "sum_total_tokens": round(sin + sout, 1),
            "sum_usd": session_cost(
                input_tokens=sin, output_tokens=sout, pricing=pricing
            )["usd"],
        }
    return out


def complexity_value_grid(
    records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Counts + avg tokens for each (complexity, value) pair."""
    rows = ledger_with_dimensions(records)
    grid: dict[str, dict[str, Any]] = {}
    for r in rows:
        dims = r.get("dimensions") or {}
        cx = dims.get("complexity", "low")
        val = dims.get("value", "low")
        key = f"{cx}×{val}"
        tin, tout = _tokens_of(r)
        cell = grid.setdefault(
            key,
            {
                "complexity": cx,
                "value": val,
                "n": 0,
                "sum_in": 0.0,
                "sum_out": 0.0,
            },
        )
        cell["n"] += 1
        cell["sum_in"] += tin
        cell["sum_out"] += tout
    for cell in grid.values():
        n = cell["n"] or 1
        cell["avg_input_tokens"] = round(cell["sum_in"] / n, 1)
        cell["avg_output_tokens"] = round(cell["sum_out"] / n, 1)
        cell["avg_total_tokens"] = round(
            (cell["sum_in"] + cell["sum_out"]) / n, 1
        )
        cost = session_cost(
            input_tokens=cell["sum_in"] / n,
            output_tokens=cell["sum_out"] / n,
        )
        cell["avg_usd"] = cost["usd"]
    return {"grid": grid}


def spend_summary(records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = ledger_with_dimensions(records)
    pricing = pricing_from_env()
    sin = sout = 0.0
    for r in rows:
        a, b = _tokens_of(r)
        sin += a
        sout += b
    cost = session_cost(input_tokens=sin, output_tokens=sout, pricing=pricing)
    cost["n_records"] = len(rows)
    return cost
