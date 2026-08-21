"""Build ordered task queue from forged PRDs (+ optional expanded variants)."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from datagen_pipeline.paths import BANK, EXPAND_DIR, QUEUE_MANIFEST, ensure_pipeline_dirs

# Categories with little/no implementation yet (cms only has task 01 done).
UNTOUCHED_CATEGORIES: tuple[str, ...] = (
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

# Full big-run category order: polish leftovers first, then untouched.
BIG_RUN_CATEGORIES: tuple[str, ...] = (
    "ai_ml",
    "games",
    *UNTOUCHED_CATEGORIES,
)

ALL_CATEGORIES: tuple[str, ...] = BIG_RUN_CATEGORIES

# Already-strong demos — skip unless --force-all. Partials/stubs stay in queue.
SKIP_DONE_KEYS: frozenset[str] = frozenset(
    {
        "ai_ml:01",  # levellens
        "ai_ml:03",  # meritlens
        "ai_ml:05",  # harborline
        "games:01",
        "games:02",
        "games:07",
        "games:08",
        "games:10",
        "cms_content:01",  # meridian
    }
)


@dataclass(frozen=True)
class QueueItem:
    task_key: str
    category: str
    index: int
    title: str
    seed_id: str
    platform_prompt: str
    workdir: str
    complexity: str
    language_runtime: str = "python"
    ui_surface: str = "static_html"
    persistence: str = "sqlite"
    variant: str | None = None
    parent_key: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _forged_dirs(cat: Path) -> list[Path]:
    forged = cat / "forged"
    if not forged.is_dir():
        return []
    dirs = [p for p in forged.iterdir() if p.is_dir() and (p / "platform_prompt.md").is_file()]

    def sort_key(p: Path) -> tuple[int, str]:
        m = re.match(r"^(\d+)_", p.name)
        return (int(m.group(1)) if m else 999, p.name)

    return sorted(dirs, key=sort_key)


def _load_seed(cat_dir: Path, index: int) -> dict | None:
    matches = list(cat_dir.glob(f"{index:02d}_*.json"))
    if not matches:
        return None
    try:
        return json.loads(matches[0].read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def iter_base_items(categories: Iterable[str]) -> list[QueueItem]:
    items: list[QueueItem] = []
    for cat in categories:
        cat_dir = BANK / cat
        if not cat_dir.is_dir():
            continue
        for forged in _forged_dirs(cat_dir):
            m = re.match(r"^(\d+)_", forged.name)
            idx = int(m.group(1)) if m else 0
            seed = _load_seed(cat_dir, idx) or {}
            title = seed.get("title") or forged.name
            seed_id = seed.get("id") or forged.name
            workdir = seed.get("workdir") or f"task_{cat}_{idx:02d}"
            hint = seed.get("dimensions_hint") or {}
            cx = hint.get("complexity") or "medium"
            items.append(
                QueueItem(
                    task_key=f"{cat}:{idx:02d}",
                    category=cat,
                    index=idx,
                    title=str(title),
                    seed_id=str(seed_id),
                    platform_prompt=str(forged / "platform_prompt.md"),
                    workdir=str(workdir),
                    complexity=str(cx),
                    language_runtime=str(hint.get("language_runtime") or "python"),
                    ui_surface=str(hint.get("ui_surface") or "static_html"),
                    persistence=str(hint.get("persistence") or "sqlite"),
                )
            )
    return items


def iter_expanded_items() -> list[QueueItem]:
    items: list[QueueItem] = []
    if not EXPAND_DIR.is_dir():
        return items
    for meta_path in sorted(EXPAND_DIR.glob("*/*/variant_meta.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        prompt = meta_path.parent / "platform_prompt.md"
        if not prompt.is_file():
            continue
        mut = meta.get("mutations") or {}
        items.append(
            QueueItem(
                task_key=str(meta["task_key"]),
                category=str(meta["category"]),
                index=int(meta["index"]),
                title=str(meta.get("title") or meta["task_key"]),
                seed_id=str(meta.get("seed_id") or meta["task_key"]),
                platform_prompt=str(prompt),
                workdir=str(meta.get("workdir") or f"task_{meta['category']}_{meta['index']:02d}"),
                complexity=str(meta.get("complexity") or "medium"),
                language_runtime=str(
                    mut.get("language_runtime") or meta.get("language_runtime") or "python"
                ),
                ui_surface=str(mut.get("ui_surface") or meta.get("ui_surface") or "static_html"),
                persistence=str(mut.get("persistence") or meta.get("persistence") or "sqlite"),
                variant=str(meta.get("variant")),
                parent_key=str(meta.get("parent_key") or ""),
            )
        )
    return items


def build_queue(
    *,
    categories: Iterable[str] | None = None,
    include_expanded: bool = True,
    skip_already_done: bool = True,
    force_all: bool = False,
) -> list[QueueItem]:
    cats = list(categories) if categories is not None else list(BIG_RUN_CATEGORIES)
    items = iter_base_items(cats)
    if include_expanded:
        cat_set = set(cats)
        items.extend([x for x in iter_expanded_items() if x.category in cat_set])
    if skip_already_done and not force_all:
        items = [x for x in items if x.task_key not in SKIP_DONE_KEYS]
    cat_rank = {c: i for i, c in enumerate(cats)}
    items.sort(
        key=lambda x: (
            cat_rank.get(x.category, 999),
            x.index,
            x.variant or "",
        )
    )
    return items


def write_manifest(items: list[QueueItem]) -> Path:
    ensure_pipeline_dirs()
    payload = {
        "count": len(items),
        "categories": sorted({i.category for i in items}),
        "languages": sorted({i.language_runtime for i in items}),
        "items": [i.to_dict() for i in items],
    }
    QUEUE_MANIFEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return QUEUE_MANIFEST
