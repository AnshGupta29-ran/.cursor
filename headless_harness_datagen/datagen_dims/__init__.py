"""Datagen dimensions: taxonomy, cross-product matrix, token/$ accounting."""

from __future__ import annotations

from datagen_dims.classify import assign_dimensions, enrich_record
from datagen_dims.budgets import COMPLEXITY_BUDGETS, budget_for, budget_prompt_line
from datagen_dims.costing import estimate_matrix_budget, pricing_from_env, session_cost
from datagen_dims.matrix import plan_matrix, write_combination_catalog
from datagen_dims.taxonomy import ALL_DIMENSIONS, taxonomy_export

__all__ = [
    "ALL_DIMENSIONS",
    "assign_dimensions",
    "enrich_record",
    "estimate_matrix_budget",
    "plan_matrix",
    "pricing_from_env",
    "session_cost",
    "taxonomy_export",
    "write_combination_catalog",
]
