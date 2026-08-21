"""Ship-gate: COMPLETE is rejected until README + smoke + seeds + source exist."""

from __future__ import annotations

from pathlib import Path

from controller.ship_gate import evaluate_ship_gate


def _write_min_demo(root: Path, *, n_py: int = 7) -> None:
    (root / "README.md").write_text(
        "# Demo\n\n```bash\npython app.py\n```\n\n"
        "Open http://localhost:8000/ after start.\n",
        encoding="utf-8",
    )
    scripts = root / "scripts"
    scripts.mkdir()
    (scripts / "smoke.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    fixtures = root / "fixtures"
    fixtures.mkdir()
    (fixtures / "seed.json").write_text('{"ok": true}\n', encoding="utf-8")
    for i in range(n_py):
        (root / f"mod_{i}.py").write_text("x = " + ("a" * 1600) + "\n", encoding="utf-8")


def test_readme_without_howto_is_not_ready(tmp_path: Path) -> None:
    _write_min_demo(tmp_path, n_py=7)
    (tmp_path / "README.md").write_text("# Demo\n\nNo run steps.\n", encoding="utf-8")
    status = evaluate_ship_gate(tmp_path, complexity="hard", language="python")
    assert status.ready is False
    assert any("how-to-run" in m for m in status.missing)


def test_thin_flask_stub_is_not_ready(tmp_path: Path) -> None:
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "app.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "index.html").write_text("<html></html>\n", encoding="utf-8")
    status = evaluate_ship_gate(tmp_path, complexity="hard", language="python")
    assert status.ready is False
    joined = " ".join(status.missing)
    assert "README.md" in joined
    assert "smoke" in joined
    assert "seed" in joined.lower() or "fixtures" in joined


def test_full_demo_is_ready(tmp_path: Path) -> None:
    _write_min_demo(tmp_path, n_py=7)
    status = evaluate_ship_gate(tmp_path, complexity="hard", language="python")
    assert status.ready is True
    assert status.source_files >= 7


def test_low_complexity_needs_fewer_files(tmp_path: Path) -> None:
    _write_min_demo(tmp_path, n_py=3)
    status = evaluate_ship_gate(tmp_path, complexity="low", language="python")
    assert status.ready is True
