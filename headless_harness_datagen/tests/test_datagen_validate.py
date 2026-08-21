"""Unit tests for datagen_pipeline.validate."""

from __future__ import annotations

import json
from pathlib import Path

from datagen_pipeline.validate import (
    check_language_lock,
    check_not_stub,
    check_structure,
    check_synthetic_seed,
    format_report,
    validate_task,
)


def _write(p: Path, text: str = "x") -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_validate_missing_workdir(tmp_path: Path, monkeypatch) -> None:
    report = validate_task(
        task_key="demo:01",
        workdir="does_not_exist_xyz",
        language_runtime="python",
        run_smoke=False,
        require_seed=False,
    )
    assert report.ok is False
    assert report.error == "workdir_missing"


def test_validate_pass_minimal_python(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "experiments" / "task_demo_01"
    _write(root / "README.md", "# Demo\n\nRun: python app.py\n\n" + ("seeded demo\n" * 20))
    _write(root / "requirements.txt", "flask\n")
    _write(
        root / "app.py",
        "from flask import Flask\napp = Flask(__name__)\n"
        "@app.get('/health')\ndef health():\n    return {'ok': True}\n"
        + ("# body\n" * 40),
    )
    _write(root / "fixtures" / "seed.json", '{"users":[{"id":1,"name":"Ada"}]}\n' * 5)
    _write(
        root / "scripts" / "smoke.py",
        "print('SMOKE PASS')\n",
    )
    monkeypatch.setattr(
        "datagen_pipeline.validate.ROOT",
        tmp_path,
    )
    monkeypatch.setattr(
        "datagen_pipeline.validate.CHAKRA_DIR",
        tmp_path / "chakra",
    )
    monkeypatch.setattr(
        "datagen_pipeline.validate.PIPELINE_DIR",
        tmp_path / "pipeline",
    )
    monkeypatch.setattr(
        "datagen_pipeline.validate.VALIDATE_DIR",
        tmp_path / "pipeline" / "validate_reports",
    )
    monkeypatch.setattr(
        "datagen_pipeline.validate.SYNTHETIC_DIR",
        tmp_path / "pipeline" / "synthetic_exports",
    )

    report = validate_task(
        task_key="demo:01",
        workdir="task_demo_01",
        language_runtime="python",
        ui_surface="api_only",
        run_smoke=True,
        require_seed=True,
        smoke_timeout=30,
    )
    print(format_report(report))
    assert report.ok is True
    assert report.resolved_root is not None
    names = {c.name: c.ok for c in report.checks}
    assert names["structure"] is True
    assert names["language_lock"] is True
    assert names["synthetic_seed"] is True
    assert names["smoke"] is True


def test_language_lock_go(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write(root / "go.mod", "module example.com/x\n")
    _write(root / "main.go", "package main\nfunc main() {}\n")
    r = check_language_lock(root, "go")
    assert r.ok is True


def test_structure_and_stub(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write(root / "README.md", "# x\n")
    _write(root / "a.py", "print(1)\n" * 50)
    _write(root / "b.py", "print(2)\n" * 50)
    _write(root / "c.py", "print(3)\n" * 50)
    assert check_structure(root).ok is True
    assert check_not_stub(root).ok is True


def test_seed_detection(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write(root / "data" / "sample.csv", "a,b\n1,2\n")
    assert check_synthetic_seed(root).ok is True


if __name__ == "__main__":
    import tempfile

    # minimal runner without pytest fixtures
    with tempfile.TemporaryDirectory() as td:
        class Fake:
            def setattr(self, name, value):
                import datagen_pipeline.validate as v
                # only used in pytest path
                pass

        # run non-monkeypatch tests
        test_language_lock_go(Path(td) / "go")
        test_structure_and_stub(Path(td) / "st")
        test_seed_detection(Path(td) / "seed")
        print("PASS local checks")
