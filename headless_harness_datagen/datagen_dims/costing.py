"""Token → money / compute-unit costing for synthetic datagen."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PricingTable:
    """USD per 1M tokens (input/output). Override via env."""

    model: str
    input_usd_per_m: float
    output_usd_per_m: float
    # Optional: provider "compute units" if billed that way
    compute_units_per_m_tokens: float = 1.0

    def cost_usd(
        self, *, input_tokens: float, output_tokens: float
    ) -> float:
        return (
            (input_tokens / 1_000_000.0) * self.input_usd_per_m
            + (output_tokens / 1_000_000.0) * self.output_usd_per_m
        )

    def compute_units(self, *, total_tokens: float) -> float:
        return (total_tokens / 1_000_000.0) * self.compute_units_per_m_tokens


def pricing_from_env(model: str | None = None) -> PricingTable:
    """
    Defaults are placeholders — set real rates in .env:

      DATAGEN_PRICE_INPUT_USD_PER_M=0.50
      DATAGEN_PRICE_OUTPUT_USD_PER_M=2.00
      DATAGEN_COMPUTE_UNITS_PER_M=1.0
    """
    model = model or os.environ.get("OPENAI_MODEL") or "kimi3"
    return PricingTable(
        model=model,
        input_usd_per_m=float(
            os.environ.get("DATAGEN_PRICE_INPUT_USD_PER_M", "0.50")
        ),
        output_usd_per_m=float(
            os.environ.get("DATAGEN_PRICE_OUTPUT_USD_PER_M", "2.00")
        ),
        compute_units_per_m_tokens=float(
            os.environ.get("DATAGEN_COMPUTE_UNITS_PER_M", "1.0")
        ),
    )


def session_cost(
    *,
    input_tokens: float | None,
    output_tokens: float | None,
    pricing: PricingTable | None = None,
) -> dict[str, Any]:
    pricing = pricing or pricing_from_env()
    tin = float(input_tokens or 0)
    tout = float(output_tokens or 0)
    total = tin + tout
    usd = pricing.cost_usd(input_tokens=tin, output_tokens=tout)
    cu = pricing.compute_units(total_tokens=total)
    return {
        "model": pricing.model,
        "input_tokens": tin,
        "output_tokens": tout,
        "total_tokens": total,
        "usd": round(usd, 6),
        "compute_units": round(cu, 6),
        "price_input_usd_per_m": pricing.input_usd_per_m,
        "price_output_usd_per_m": pricing.output_usd_per_m,
    }


def estimate_matrix_budget(
    *,
    n_combinations: int,
    examples_per_combo: int,
    avg_input_tokens: float,
    avg_output_tokens: float,
    pricing: PricingTable | None = None,
) -> dict[str, Any]:
    pricing = pricing or pricing_from_env()
    n = n_combinations * examples_per_combo
    tin = n * avg_input_tokens
    tout = n * avg_output_tokens
    cost = session_cost(
        input_tokens=tin, output_tokens=tout, pricing=pricing
    )
    cost["n_combinations"] = n_combinations
    cost["examples_per_combo"] = examples_per_combo
    cost["n_examples"] = n
    cost["avg_input_tokens"] = avg_input_tokens
    cost["avg_output_tokens"] = avg_output_tokens
    return cost
