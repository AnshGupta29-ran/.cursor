"""Queue-advance helpers for build-first autopilot."""

from __future__ import annotations

from pathlib import Path

from datagen_pipeline.autopilot import _workdir_looks_built
from datagen_pipeline.queue import QueueItem


def _item(workdir: str, *, language: str = "rust", complexity: str = "low") -> QueueItem:
    return QueueItem(
        task_key="cms_content:06",
        category="cms_content",
        index=6,
        title="Internal wiki",
        seed_id="x",
        platform_prompt="platform_prompt.md",
        workdir=workdir,
        complexity=complexity,
        language_runtime=language,
    )


def test_three_source_files_alone_are_not_built(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "lib.rs").write_text("fn x() {}", encoding="utf-8")
    (src / "main.rs").write_text("fn main() {}", encoding="utf-8")
    (src / "handlers.rs").write_text("fn h() {}", encoding="utf-8")
    assert _workdir_looks_built(_item(str(tmp_path))) is False


def test_shippable_demo_is_built(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# wiki\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "smoke.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    (tmp_path / "fixtures").mkdir()
    (tmp_path / "fixtures" / "seed.json").write_text("{}\n", encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    blob = "fn x() { let _s = \"" + ("a" * 900) + "\"; }\n"
    (src / "lib.rs").write_text(blob, encoding="utf-8")
    (src / "main.rs").write_text(blob, encoding="utf-8")
    (src / "handlers.rs").write_text(blob, encoding="utf-8")
    assert _workdir_looks_built(_item(str(tmp_path))) is True


def test_markdown_alone_is_not_built(tmp_path: Path) -> None:
    (tmp_path / "plan.md").write_text("# plan", encoding="utf-8")
    (tmp_path / "platform_prompt.md").write_text("# prd", encoding="utf-8")
    (tmp_path / "HARNESS_POLICY.md").write_text("# policy", encoding="utf-8")
    assert _workdir_looks_built(_item(str(tmp_path))) is False
