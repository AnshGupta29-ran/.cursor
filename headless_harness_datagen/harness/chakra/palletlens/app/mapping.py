"""Versioned ImageNet-label → refurb-category mapping table."""
from dataclasses import dataclass, field

import yaml

VALID_ROUTING = {"bench_test", "parts_harvest", "certified_recycle", "manual_sort"}
UNMAPPED_CATEGORY = "unmapped_general"


@dataclass(frozen=True)
class CategoryMap:
    version: str
    label_map: dict[str, str]
    categories: dict[str, dict]
    # routing hint per category, resolved at load
    routing_by_category: dict[str, str] = field(default_factory=dict)

    def category_for(self, imagenet_label: str) -> str:
        return self.label_map.get(imagenet_label, UNMAPPED_CATEGORY)

    def routing_for(self, category: str) -> str:
        return self.routing_by_category.get(
            category, self.routing_by_category[UNMAPPED_CATEGORY]
        )


def load_category_map(path: str) -> CategoryMap:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    version = str(raw["version"])
    label_map: dict[str, str] = dict(raw.get("label_map") or {})
    categories: dict[str, dict] = dict(raw.get("categories") or {})

    if UNMAPPED_CATEGORY not in categories:
        categories[UNMAPPED_CATEGORY] = {
            "routing": "manual_sort",
            "description": "Anything without a curated mapping.",
        }

    routing_by_category: dict[str, str] = {}
    for name, meta in categories.items():
        routing = (meta or {}).get("routing", "manual_sort")
        if routing not in VALID_ROUTING:
            raise ValueError(f"Category {name!r} has invalid routing {routing!r}")
        routing_by_category[name] = routing

    for label, category in label_map.items():
        if category not in categories:
            raise ValueError(f"label_map entry {label!r} → unknown category {category!r}")

    return CategoryMap(
        version=version,
        label_map=label_map,
        categories=categories,
        routing_by_category=routing_by_category,
    )
