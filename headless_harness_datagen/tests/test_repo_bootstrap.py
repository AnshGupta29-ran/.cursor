"""Unit tests for project git bootstrap."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from controller.repo_bootstrap import ensure_project_git_repo


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_fresh_dir_initializes_git_with_head() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "project"
        result = ensure_project_git_repo(repo)
        assert result.error is None
        assert result.initialized is True
        assert result.already_ready is False
        assert (repo / ".git").exists()
        head = _git(repo, "rev-parse", "HEAD")
        assert head
        assert Path(_git(repo, "rev-parse", "--show-toplevel")).resolve() == repo.resolve()
        gi = (repo / ".gitignore").read_text(encoding="utf-8")
        assert "target/" in gi
        assert "node_modules/" in gi


def test_second_call_is_idempotent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "project"
        first = ensure_project_git_repo(repo)
        assert first.initialized is True
        head_before = _git(repo, "rev-list", "--count", "HEAD")
        second = ensure_project_git_repo(repo)
        assert second.error is None
        assert second.already_ready is True
        assert second.initialized is False
        head_after = _git(repo, "rev-list", "--count", "HEAD")
        assert head_before == head_after == "1"


def test_existing_git_with_head_skips_init() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "project"
        repo.mkdir(parents=True)
        _git(repo, "init")
        _git(repo, "config", "user.email", "test@example.com")
        _git(repo, "config", "user.name", "Test")
        _git(repo, "commit", "--allow-empty", "-m", "seed")
        result = ensure_project_git_repo(repo)
        assert result.error is None
        assert result.already_ready is True
        assert result.initialized is False
        assert "target/" in (repo / ".gitignore").read_text(encoding="utf-8")


def test_scrubs_cargo_target_tree() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "project"
        dumped = repo / "target" / "debug" / "deps"
        dumped.mkdir(parents=True)
        (dumped / "junk.rlib").write_text("x", encoding="utf-8")
        result = ensure_project_git_repo(repo)
        assert result.error is None
        assert not (repo / "target").exists()


def test_git_dir_without_head_gets_empty_commit() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "project"
        repo.mkdir(parents=True)
        _git(repo, "init")
        # Fresh init has no commits; ensure_project_git_repo should create HEAD.
        result = ensure_project_git_repo(repo)
        assert result.error is None
        assert result.initialized is True
        assert _git(repo, "rev-parse", "HEAD")


def main() -> int:
    tests = [
        test_fresh_dir_initializes_git_with_head,
        test_second_call_is_idempotent,
        test_existing_git_with_head_skips_init,
        test_scrubs_cargo_target_tree,
        test_git_dir_without_head_gets_empty_commit,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {test.__name__}: {exc}")
    if failed:
        print(f"\n{failed} test(s) failed")
        return 1
    print(f"\nAll {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
