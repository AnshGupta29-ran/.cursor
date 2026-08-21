"""Reject IMPLEMENTATION_STATUS: COMPLETE until the workdir is a real demo."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = {
    ".git",
    "node_modules",
    "bin",
    "obj",
    "target",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
}

CODE_EXTS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".cs",
    ".cpp",
    ".cc",
    ".c",
    ".h",
    ".hpp",
    ".rs",
    ".go",
    ".java",
    ".kt",
    ".html",
    ".css",
}

LANG_EXTS: dict[str, tuple[str, ...]] = {
    "python": (".py",),
    "javascript": (".js", ".jsx", ".mjs", ".cjs"),
    "typescript": (".ts", ".tsx"),
    "go": (".go",),
    "rust": (".rs",),
    "java": (".java",),
    "csharp": (".cs",),
    "cpp": (".cpp", ".cc", ".cxx", ".hpp", ".h", ".c"),
}

SMOKE_NAMES = (
    "scripts/smoke.py",
    "scripts/smoke.sh",
    "scripts/smoke.ps1",
    "scripts/smoke.bat",
    "scripts/smoke.js",
    "scripts/smoke.ts",
    "scripts/smoke.rs",
    "smoke.py",
    "smoke.sh",
    "tests/smoke.py",
    "tests/smoke.rs",
    "tests/smoke_test.rs",
)

SEED_HINTS = (
    "fixtures",
    "fixture",
    "seed",
    "seeds",
    "sample_data",
    "sample-data",
    "testdata",
    "test_data",
    "demo_data",
    "synthetic",
    "data",
)

MIN_SOURCE_FILES = {"low": 3, "medium": 5, "hard": 7}
MIN_SOURCE_BYTES = {"low": 2500, "medium": 6000, "hard": 10000}


@dataclass(frozen=True)
class ShipStatus:
    ready: bool
    missing: tuple[str, ...]
    source_files: int
    source_bytes: int

    def nudge(self) -> str:
        if self.ready:
            return ""
        lines = ", ".join(self.missing) if self.missing else "more source"
        return (
            f"IMPLEMENTATION_STATUS: COMPLETE is rejected until the demo is shippable. "
            f"Still missing: {lines}. "
            f"Write README.md with how-to-run (cargo/npm/python command AND "
            f"http://localhost:PORT or explicit CLI-only note), "
            f"a smoke script (scripts/smoke.py OR scripts/smoke.sh OR scripts/smoke.js "
            f"OR tests/smoke.rs), fixtures/ or data/ seed files, and enough source. "
            f"Do not spawn Agent/Plan/Explore. Do not ls. Call Write now."
        )


_RUN_HINT_RE = re.compile(
    r"(cargo\s+run|npm\s+(run|start)|pnpm\s+|yarn\s+|python\s+|uvicorn\s+|"
    r"node\s+|go\s+run|dotnet\s+run|mvn\s+|gradlew?\b|make\s+|"
    r"scripts[/\\]smoke|smoke\.(py|sh|js|ts)|docker\s+compose)",
    re.IGNORECASE,
)
_URL_OR_CLI_RE = re.compile(
    r"(https?://(localhost|127\.0\.0\.1)(:\d+)?(/[\w./-]*)?"
    r"|CLI only|command[- ]line|no browser)",
    re.IGNORECASE,
)


def _readme_has_howto(text: str) -> bool:
    body = text or ""
    if not _RUN_HINT_RE.search(body):
        return False
    return bool(_URL_OR_CLI_RE.search(body))


def _iter_files(root: Path) -> list[Path]:
    out: list[Path] = []
    if not root.is_dir():
        return out
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        out.append(path)
    return out


def evaluate_ship_gate(
    root: str | Path,
    *,
    complexity: str | None = None,
    language: str | None = None,
) -> ShipStatus:
    repo = Path(root)
    cx = (complexity or os.environ.get("HARNESS_COMPLEXITY") or "medium").strip().lower()
    if cx not in MIN_SOURCE_FILES:
        cx = "medium"
    lang = (language or os.environ.get("HARNESS_LANGUAGE") or "").strip().lower()

    files = _iter_files(repo)
    missing: list[str] = []

    has_readme = any(p.name.lower() == "readme.md" for p in files)
    if not has_readme:
        missing.append("README.md")
    else:
        readme_path = next(p for p in files if p.name.lower() == "readme.md")
        try:
            readme_text = readme_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            readme_text = ""
        if not _readme_has_howto(readme_text):
            missing.append(
                "README how-to-run (run command + localhost URL or 'CLI only')"
            )

    has_smoke = False
    for rel in SMOKE_NAMES:
        if (repo / rel).is_file():
            has_smoke = True
            break
    pkg = repo / "package.json"
    if pkg.is_file():
        try:
            text = pkg.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            text = ""
        if '"smoke"' in text:
            has_smoke = True
    if not has_smoke:
        missing.append("scripts/smoke.py")

    has_seed = False
    for path in files:
        parts_l = [x.lower() for x in path.parts]
        name_l = path.name.lower()
        if any(h in parts_l or h in name_l for h in SEED_HINTS):
            if path.suffix.lower() in {
                ".json",
                ".jsonl",
                ".csv",
                ".sql",
                ".md",
                ".txt",
                ".yaml",
                ".yml",
            } or "seed" in name_l or "fixture" in name_l:
                has_seed = True
                break
    if not has_seed:
        missing.append("fixtures/ or data/ seed files")

    sources = [p for p in files if p.suffix.lower() in CODE_EXTS]
    source_bytes = 0
    for path in sources:
        try:
            source_bytes += path.stat().st_size
        except OSError:
            continue

    need_n = MIN_SOURCE_FILES[cx]
    if len(sources) < need_n:
        missing.append(f">={need_n} source files (have {len(sources)}, complexity={cx})")
    need_b = MIN_SOURCE_BYTES[cx]
    if source_bytes < need_b:
        missing.append(f">={need_b} bytes of source (have {source_bytes})")

    lang_exts = LANG_EXTS.get(lang, ())
    if lang_exts:
        lang_n = sum(1 for p in sources if p.suffix.lower() in lang_exts)
        if lang_n < 1:
            missing.append(f"{lang} source ({', '.join(lang_exts)})")

    return ShipStatus(
        ready=not missing,
        missing=tuple(missing),
        source_files=len(sources),
        source_bytes=source_bytes,
    )


def pipeline_mode() -> bool:
    return os.environ.get("DATAGEN_PIPELINE_MODE", "").strip() == "1"
