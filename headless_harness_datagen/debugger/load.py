"""Load pipeline artifacts for offline debugging."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from controller.trace_replay import (
    ConversationReplay,
    load_trace_bundle,
    reconstruct_conversation,
)


@dataclass
class LoadedRun:
    """In-memory view of a completed (or mid-run) pipeline directory."""

    pipeline_dir: Path
    run_id: str | None
    bundle: dict[str, Any]
    replay: ConversationReplay
    summary: dict[str, Any] = field(default_factory=dict)
    verdict: dict[str, Any] = field(default_factory=dict)

    @property
    def normalized(self) -> list[dict[str, Any]]:
        return list(self.bundle.get("normalized") or [])

    @property
    def raw(self) -> list[dict[str, Any]]:
        return list(self.bundle.get("raw") or [])


def resolve_pipeline_dir(path: Path | str) -> Path:
    """
    Accept logs/<run_id>, logs/<run_id>/pipeline, or .../pipeline/working.

    Prefer finalized artifact dir when both working/ and parent exist.
    """
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"run path not found: {root}")

    if root.name == "working" and (root.parent / "trace.jsonl").is_file():
        return root.parent
    if root.name == "pipeline" and (root / "trace.jsonl").is_file():
        return root
    if (root / "pipeline" / "trace.jsonl").is_file():
        return root / "pipeline"
    if (root / "trace.jsonl").is_file():
        return root
    if (root / "pipeline" / "working" / "trace.jsonl").is_file():
        return root / "pipeline" / "working"
    if (root / "working" / "trace.jsonl").is_file():
        return root / "working"
    raise FileNotFoundError(
        f"no trace.jsonl under {root} (expected pipeline/ or pipeline/working/)"
    )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def load_run(path: Path | str) -> LoadedRun:
    """Load summary, verdict, and dual-channel traces for analysis."""
    pipeline_dir = resolve_pipeline_dir(path)
    bundle = load_trace_bundle(pipeline_dir)
    # Mid-run: fall back to working/ traces if parent artifact traces empty.
    if not bundle.get("normalized") and (pipeline_dir / "working").is_dir():
        working = load_trace_bundle(pipeline_dir / "working")
        if working.get("normalized"):
            bundle = working
            pipeline_dir = pipeline_dir / "working"

    replay = reconstruct_conversation(bundle=bundle)
    summary = _read_json(pipeline_dir / "summary.json")
    if not summary and pipeline_dir.name == "working":
        summary = _read_json(pipeline_dir.parent / "summary.json")
    verdict = _read_json(pipeline_dir / "verdict.json")
    if not verdict and pipeline_dir.name == "working":
        verdict = _read_json(pipeline_dir.parent / "verdict.json")

    run_id = (
        summary.get("run_id")
        or replay.run_id
        or pipeline_dir.parent.parent.name
        if pipeline_dir.name == "pipeline"
        else pipeline_dir.parent.name
    )
    if pipeline_dir.name == "working":
        run_id = summary.get("run_id") or pipeline_dir.parent.parent.name

    return LoadedRun(
        pipeline_dir=pipeline_dir,
        run_id=str(run_id) if run_id else None,
        bundle=bundle,
        replay=replay,
        summary=summary,
        verdict=verdict,
    )
