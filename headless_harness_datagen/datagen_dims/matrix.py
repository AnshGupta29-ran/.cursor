"""Cross-product planning over dimension axes."""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any, Iterable, Iterator

from datagen_dims.taxonomy import (
    DIMENSIONS_BY_ID,
    Dimension,
    STARTER_FILTERS,
    core_matrix_axes,
    matrix_axes,
    taxonomy_export,
)


def product_count(axes: Iterable[Dimension]) -> int:
    n = 1
    for d in axes:
        n *= max(1, len(d.values))
    return n


def iter_combinations(
    axes: list[Dimension] | None = None,
    *,
    include_optional: bool = False,
    filters: dict[str, set[str]] | None = None,
) -> Iterator[dict[str, str]]:
    """Yield one dict per cross-product cell."""
    axes = axes or core_matrix_axes()
    filters = filters or {}
    value_lists: list[list[str]] = []
    ids: list[str] = []
    for d in axes:
        vals = list(d.values)
        if d.id in filters and filters[d.id]:
            vals = [v for v in vals if v in filters[d.id]]
        if not vals:
            return
        ids.append(d.id)
        value_lists.append(vals)
    for combo in itertools.product(*value_lists):
        yield dict(zip(ids, combo))


def plan_matrix(
    *,
    include_optional: bool = False,
    full: bool = False,
    starter: bool = True,
    filters: dict[str, set[str]] | None = None,
    axes_ids: list[str] | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    if axes_ids:
        axes = [DIMENSIONS_BY_ID[i] for i in axes_ids]
    elif full:
        axes = matrix_axes(include_optional=include_optional)
    else:
        axes = core_matrix_axes()
    merged_filters: dict[str, set[str]] | None
    if filters:
        merged_filters = dict(filters)
    elif starter and not full and not axes_ids:
        merged_filters = {k: set(v) for k, v in STARTER_FILTERS.items()}
    else:
        merged_filters = None
    total = sum(
        1
        for _ in iter_combinations(
            axes, include_optional=include_optional, filters=merged_filters
        )
    )
    sample: list[dict[str, str]] = []
    for i, combo in enumerate(
        iter_combinations(
            axes, include_optional=include_optional, filters=merged_filters
        )
    ):
        if limit is not None and i >= limit:
            break
        sample.append(combo)
    mode = "full" if full and not axes_ids else ("custom" if axes_ids else "core_starter")
    return {
        "mode": mode,
        "axes": [
            {"id": d.id, "n_values": len(d.values), "values": list(d.values)}
            for d in axes
        ],
        "filters_applied": {
            k: sorted(v) for k, v in (merged_filters or {}).items()
        },
        "n_combinations": total,
        "unfiltered_product": product_count(axes),
        "sample": sample,
        "taxonomy_layers": taxonomy_export()["layers"],
        "note": (
            "Default starter filters keep the matrix around a few thousand cells. "
            "Pass starter=False / --all-core for the full core cartesian product, "
            "or --full (huge) with --filter."
        ),
    }


def write_combination_catalog(
    path: Path,
    *,
    include_optional: bool = False,
    full: bool = False,
    starter: bool = True,
    filters: dict[str, set[str]] | None = None,
    axes_ids: list[str] | None = None,
    examples_per_combo: int = 1,
) -> tuple[Path, int]:
    """Write JSONL of combination specs for batch generation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if axes_ids:
        axes = [DIMENSIONS_BY_ID[i] for i in axes_ids]
    elif full:
        axes = matrix_axes(include_optional=include_optional)
    else:
        axes = core_matrix_axes()
    if filters:
        merged = dict(filters)
    elif starter and not full and not axes_ids:
        merged = {k: set(v) for k, v in STARTER_FILTERS.items()}
    else:
        merged = None
    n = 0
    with path.open("w", encoding="utf-8") as fh:
        for combo in iter_combinations(
            axes, include_optional=include_optional, filters=merged
        ):
            for k in range(examples_per_combo):
                row = {
                    "combo_id": _combo_id(combo),
                    "example_index": k,
                    "dimensions": combo,
                    "seed_hint": _seed_hint(combo),
                }
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                n += 1
    return path, n


def _combo_id(combo: dict[str, str]) -> str:
    return "|".join(f"{k}={v}" for k, v in sorted(combo.items()))


def _seed_hint(combo: dict[str, str]) -> str:
    task = combo.get("task_family", "coding_implement")
    domain = combo.get("business_domain", "general_utilities")
    lang = combo.get("language_runtime", "python")
    art = combo.get("artifact_type", "web_fullstack")
    cx = combo.get("complexity", "medium")
    return (
        f"Build a {cx}-complexity {art.replace('_', ' ')} in {lang} "
        f"for the {domain.replace('_', ' ')} domain; "
        f"primary task={task.replace('_', ' ')}."
    )
