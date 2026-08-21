from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "artifacts" / "datagen_task_bank" / "by_category"
PIPELINE_DIR = ROOT / "artifacts" / "datagen_pipeline"
CHECKPOINT_PATH = PIPELINE_DIR / "checkpoint.json"
QUEUE_MANIFEST = PIPELINE_DIR / "queue_manifest.json"
EXPAND_DIR = PIPELINE_DIR / "expanded"
CHAKRA_DIR = ROOT / "harness" / "chakra"
NEXT_PROMPT_PATH = PIPELINE_DIR / "CHAKRA_NEXT_TASK.md"
STATUS_PATH = PIPELINE_DIR / "STATUS.md"


def ensure_pipeline_dirs() -> None:
    PIPELINE_DIR.mkdir(parents=True, exist_ok=True)
    EXPAND_DIR.mkdir(parents=True, exist_ok=True)
