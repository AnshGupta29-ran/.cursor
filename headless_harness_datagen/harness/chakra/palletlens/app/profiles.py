"""Threshold profiles: decide auto-route vs. review queue."""
from dataclasses import dataclass

import yaml


@dataclass(frozen=True)
class ThresholdProfile:
    name: str
    min_top1_confidence: float
    min_margin_over_runner_up: float
    default_routing: str
    description: str = ""

    def evaluate(self, top1_confidence: float, runner_up_confidence: float) -> str | None:
        """Return None if the prediction passes (auto-route), else a machine-readable reason."""
        margin = top1_confidence - runner_up_confidence
        if top1_confidence < self.min_top1_confidence:
            return "below_threshold"
        if margin < self.min_margin_over_runner_up:
            return "ambiguous_margin"
        return None


def load_profiles(path: str) -> dict[str, ThresholdProfile]:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    profiles: dict[str, ThresholdProfile] = {}
    for name, spec in (raw.get("profiles") or {}).items():
        profiles[name] = ThresholdProfile(
            name=name,
            min_top1_confidence=float(spec["min_top1_confidence"]),
            min_margin_over_runner_up=float(spec.get("min_margin_over_runner_up", 0.0)),
            default_routing=str(spec.get("default_routing", "manual_sort")),
            description=str(spec.get("description", "")),
        )
    if not profiles:
        raise ValueError(f"No threshold profiles defined in {path}")
    return profiles
