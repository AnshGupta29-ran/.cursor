"""Deterministic post-build validation for datagen tasks.

Runs AFTER main.py / interactive Chakra claims DONE, BEFORE checkpoint mark_done.
Checks structure, language lock, smoke/tests, optional HTTP health, and seed/synthetic data.

Usage:
  python -m datagen_pipeline validate --key cms_content:04
  python -m datagen_pipeline validate --workdir task_cms_content_04 --language csharp
"""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from datagen_pipeline.paths import CHAKRA_DIR, PIPELINE_DIR, ROOT, ensure_pipeline_dirs

VALIDATE_DIR = PIPELINE_DIR / "validate_reports"
SYNTHETIC_DIR = PIPELINE_DIR / "synthetic_exports"

LANG_MARKERS: dict[str, tuple[str, ...]] = {
    "python": ("requirements.txt", "pyproject.toml", "Pipfile", "setup.py"),
    "typescript": ("package.json", "tsconfig.json"),
    "javascript": ("package.json",),
    "go": ("go.mod",),
    "rust": ("Cargo.toml",),
    "java": ("pom.xml", "build.gradle", "build.gradle.kts"),
    "csharp": (".csproj", ".sln"),
    "cpp": ("CMakeLists.txt", "Makefile", "meson.build", "compile_flags.txt"),
}

SOURCE_GLOBS: dict[str, tuple[str, ...]] = {
    "python": ("**/*.py",),
    "typescript": ("**/*.{ts,tsx}",),
    "javascript": ("**/*.{js,jsx,mjs,cjs}",),
    "go": ("**/*.go",),
    "rust": ("**/*.rs",),
    "java": ("**/*.java",),
    "csharp": ("**/*.cs",),
    "cpp": ("**/*.{cpp,cc,cxx,hpp,h,c}",),
}

SMOKE_CANDIDATES = (
    "scripts/smoke.py",
    "smoke.py",
    "scripts/smoke.sh",
    "scripts/smoke.bat",
    "scripts/smoke.ps1",
    "tests/smoke.ps1",
    "tests/smoke.py",
    "tests/smoke.sh",
    "tests/smoke.bat",
    "scripts/smoke.js",
    "scripts/smoke.ts",
    "scripts/smoke.mjs",
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
    "data",
    "demo_data",
    "synthetic",
)


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidateReport:
    task_key: str
    workdir: str
    resolved_root: str | None
    language_runtime: str
    ui_surface: str
    ok: bool
    checks: list[CheckResult] = field(default_factory=list)
    smoke_ran: bool = False
    http_checked: bool = False
    started_at: str = ""
    finished_at: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_key": self.task_key,
            "workdir": self.workdir,
            "resolved_root": self.resolved_root,
            "language_runtime": self.language_runtime,
            "ui_surface": self.ui_surface,
            "ok": self.ok,
            "smoke_ran": self.smoke_ran,
            "http_checked": self.http_checked,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
            "checks": [asdict(c) for c in self.checks],
        }


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_task_root(workdir: str) -> Path | None:
    """Find where the agent actually wrote the demo."""
    raw = Path(workdir)
    candidates: list[Path] = []
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.extend(
            [
                ROOT / "experiments" / workdir,
                CHAKRA_DIR / workdir,
                ROOT / workdir,
                CHAKRA_DIR / Path(workdir).name,
            ]
        )
        # also try without task_ prefix variants
        name = Path(workdir).name
        if name.startswith("task_"):
            candidates.append(CHAKRA_DIR / name.replace("task_", "", 1))

    best: Path | None = None
    best_score = -1
    for c in candidates:
        if not c.is_dir():
            continue
        score = _repo_score(c)
        if score > best_score:
            best_score = score
            best = c
    if best is None or best_score <= 0:
        return None
    return best.resolve()


def _repo_score(root: Path) -> int:
    score = 0
    names = {p.name.lower() for p in root.iterdir()} if root.is_dir() else set()
    for marker in (
        "readme.md",
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "go.mod",
        "cargo.toml",
        "cmakelists.txt",
        "pom.xml",
        "app.py",
        "main.py",
        "main.go",
        "main.rs",
        "dev.sh",
        "dev.bat",
    ):
        if marker in names:
            score += 3
    # source files
    for pat in ("*.py", "*.ts", "*.tsx", "*.js", "*.go", "*.rs", "*.cs", "*.java", "*.cpp"):
        try:
            score += min(5, len(list(root.glob(pat))))
        except OSError:
            pass
    # ignore empty / almost empty dirs
    try:
        n_files = sum(1 for _ in root.rglob("*") if _.is_file())
    except OSError:
        n_files = 0
    if n_files < 2:
        return 0
    score += min(10, n_files // 3)
    return score


def _has_any(root: Path, names: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for name in names:
        if name.startswith("."):
            # extension match e.g. .csproj
            hits = list(root.rglob(f"*{name}"))[:5]
            if hits:
                found.extend(str(h.relative_to(root)) for h in hits)
        else:
            p = root / name
            if p.is_file():
                found.append(name)
            else:
                # case-insensitive top-level
                for child in root.iterdir():
                    if child.is_file() and child.name.lower() == name.lower():
                        found.append(child.name)
                        break
    return found


def _count_sources(root: Path, language: str) -> int:
    pats = SOURCE_GLOBS.get(language.lower(), ("**/*",))
    n = 0
    skip = {".git", "node_modules", "dist", "build", "__pycache__", ".venv", "venv", "target"}
    for pat in pats:
        # pathlib doesn't expand {a,b}; expand manually
        if "{" in pat:
            m = re.search(r"\{([^}]+)\}", pat)
            if not m:
                continue
            prefix = pat[: m.start()]
            suffix = pat[m.end() :]
            for ext in m.group(1).split(","):
                for p in root.glob(f"{prefix}{ext}{suffix}"):
                    if any(part in skip for part in p.parts):
                        continue
                    if p.is_file():
                        n += 1
        else:
            for p in root.glob(pat):
                if any(part in skip for part in p.parts):
                    continue
                if p.is_file():
                    n += 1
    return n


def check_structure(root: Path) -> CheckResult:
    readme = None
    for name in ("README.md", "Readme.md", "readme.md"):
        if (root / name).is_file():
            readme = name
            break
    try:
        n_files = sum(1 for p in root.rglob("*") if p.is_file())
    except OSError:
        n_files = 0
    ok = bool(readme) and n_files >= 3
    return CheckResult(
        name="structure",
        ok=ok,
        detail=f"readme={readme or 'MISSING'} files={n_files}",
        evidence={"readme": readme, "file_count": n_files},
    )


def check_language_lock(root: Path, language: str) -> CheckResult:
    lang = (language or "python").lower().strip()
    markers = LANG_MARKERS.get(lang, ())
    found = _has_any(root, markers) if markers else []
    src_n = _count_sources(root, lang)

    # csharp/cpp markers are extensions
    if lang == "csharp" and not found:
        found = [str(p.relative_to(root)) for p in list(root.rglob("*.csproj"))[:3]]
        found += [str(p.relative_to(root)) for p in list(root.rglob("*.sln"))[:2]]
    if lang == "cpp" and not found:
        for name in ("CMakeLists.txt", "Makefile", "meson.build"):
            hits = list(root.rglob(name))[:2]
            found.extend(str(h.relative_to(root)) for h in hits)

    ok = bool(found) or src_n >= 2
    # Soft-fail only when clearly wrong stack dominates (e.g. lock=rust but only package.json + zero .rs)
    wrong = False
    if lang not in {"javascript", "typescript"} and (root / "package.json").is_file() and src_n == 0:
        # might be a hybrid UI — only wrong if no primary sources
        if lang in {"rust", "go", "java", "csharp", "cpp"} and not found:
            wrong = True
    if lang == "python" and not found and src_n == 0:
        wrong = True
        ok = False
    if wrong:
        ok = False

    return CheckResult(
        name="language_lock",
        ok=ok,
        detail=f"lang={lang} markers={found[:5] or 'none'} sources={src_n}",
        evidence={"language": lang, "markers": found[:10], "source_count": src_n},
    )


def check_synthetic_seed(root: Path) -> CheckResult:
    hits: list[str] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        parts_l = [x.lower() for x in p.parts]
        name_l = p.name.lower()
        if any(h in parts_l or h in name_l for h in SEED_HINTS):
            if p.suffix.lower() in {
                ".json",
                ".jsonl",
                ".csv",
                ".tsv",
                ".sql",
                ".md",
                ".txt",
                ".yaml",
                ".yml",
                ".sqlite",
                ".db",
            } or "seed" in name_l or "fixture" in name_l:
                try:
                    rel = str(p.relative_to(root))
                except ValueError:
                    rel = str(p)
                if "node_modules" in rel or ".git" in rel:
                    continue
                hits.append(rel)
                if len(hits) >= 12:
                    break
    # Also accept inline seed scripts
    for pat in ("**/seed*.py", "**/seed*.js", "**/seed*.ts", "**/seed*.sh", "**/seed*.bat"):
        for p in root.glob(pat):
            if p.is_file() and "node_modules" not in p.parts:
                hits.append(str(p.relative_to(root)))
    ok = len(hits) >= 1
    return CheckResult(
        name="synthetic_seed",
        ok=ok,
        detail=f"seed_files={len(hits)}",
        evidence={"files": hits[:12]},
    )


def _find_smoke(root: Path) -> Path | None:
    for rel in SMOKE_CANDIDATES:
        p = root / rel
        if p.is_file():
            return p
    # package.json scripts.smoke
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            scripts = data.get("scripts") or {}
            if "smoke" in scripts:
                return pkg  # sentinel: run npm run smoke
        except json.JSONDecodeError:
            pass
    return None


def _run(cmd: list[str], *, cwd: Path, timeout: int, env: dict[str, str] | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env or os.environ.copy(),
            shell=False,
        )
        out = (proc.stdout or "")[-4000:] + "\n" + (proc.stderr or "")[-2000:]
        return proc.returncode, out.strip()
    except subprocess.TimeoutExpired as exc:
        return 124, f"timeout after {timeout}s: {exc}"
    except OSError as exc:
        return 127, str(exc)


def check_smoke(root: Path, *, timeout: int = 120) -> CheckResult:
    smoke = _find_smoke(root)
    if smoke is None:
        # Fallbacks that still prove the platform runs
        if (root / "test_app.py").is_file():
            rc, out = _run(
                [os.environ.get("PYTHON", "python"), "test_app.py", "-q"],
                cwd=root,
                timeout=timeout,
            )
            return CheckResult(
                name="smoke",
                ok=rc == 0,
                detail=f"fallback test_app.py rc={rc}",
                evidence={"cmd": "python test_app.py -q", "output_tail": out[-1500:]},
            )
        # pytest if tests/ exists
        if (root / "tests").is_dir() or list(root.glob("test_*.py")):
            rc, out = _run(
                [os.environ.get("PYTHON", "python"), "-m", "pytest", "-q", "--maxfail=1"],
                cwd=root,
                timeout=timeout,
            )
            if rc == 0:
                return CheckResult(
                    name="smoke",
                    ok=True,
                    detail="fallback pytest -q rc=0",
                    evidence={"cmd": "python -m pytest -q", "output_tail": out[-1500:]},
                )
        if (root / "package.json").is_file():
            try:
                pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pkg = {}
            scripts = pkg.get("scripts") or {}
            for name in ("test", "build"):
                if name in scripts:
                    rc, out = _run(["npm", "run", name], cwd=root, timeout=timeout)
                    return CheckResult(
                        name="smoke",
                        ok=rc == 0,
                        detail=f"fallback npm run {name} rc={rc}",
                        evidence={"cmd": f"npm run {name}", "output_tail": out[-1500:]},
                    )
        # Dev script presence alone is NOT enough — require an executable check.
        # Generate a tiny ephemeral smoke if app.py + fixtures exist (python demos).
        if (root / "app.py").is_file() and (
            (root / "fixtures").is_dir() or (root / "data").is_dir()
        ):
            rc, out = _run(
                [
                    os.environ.get("PYTHON", "python"),
                    "-c",
                    "import importlib.util,sys; "
                    "spec=importlib.util.spec_from_file_location('app','app.py'); "
                    "m=importlib.util.module_from_spec(spec); "
                    "spec.loader.exec_module(m); print('IMPORT_OK')",
                ],
                cwd=root,
                timeout=min(60, timeout),
            )
            return CheckResult(
                name="smoke",
                ok=rc == 0 and "IMPORT_OK" in out,
                detail=f"fallback import app.py rc={rc}",
                evidence={"cmd": "python -c import app", "output_tail": out[-1500:]},
            )
        return CheckResult(
            name="smoke",
            ok=False,
            detail="no smoke.py / scripts/smoke / npm smoke / tests found",
            evidence={},
        )

    if smoke.name == "package.json":
        rc, out = _run(["npm", "run", "smoke"], cwd=root, timeout=timeout)
        return CheckResult(
            name="smoke",
            ok=rc == 0,
            detail=f"npm run smoke rc={rc}",
            evidence={"cmd": "npm run smoke", "output_tail": out[-1500:]},
        )

    if smoke.suffix == ".py":
        rel = str(smoke.relative_to(root))
        rc, out = _run(
            [os.environ.get("PYTHON", "python"), rel],
            cwd=root,
            timeout=timeout,
        )
        return CheckResult(
            name="smoke",
            ok=rc == 0,
            detail=f"python {rel} rc={rc}",
            evidence={"cmd": f"python {rel}", "output_tail": out[-1500:]},
        )

    if smoke.suffix in {".sh"}:
        rc, out = _run(["bash", str(smoke)], cwd=root, timeout=timeout)
        return CheckResult(
            name="smoke",
            ok=rc == 0,
            detail=f"bash {smoke.name} rc={rc}",
            evidence={"cmd": f"bash {smoke}", "output_tail": out[-1500:]},
        )

    if smoke.suffix in {".bat", ".cmd"}:
        rc, out = _run(["cmd", "/c", str(smoke)], cwd=root, timeout=timeout)
        return CheckResult(
            name="smoke",
            ok=rc == 0,
            detail=f"cmd {smoke.name} rc={rc}",
            evidence={"cmd": str(smoke), "output_tail": out[-1500:]},
        )

    if smoke.suffix == ".ps1":
        rc, out = _run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(smoke),
            ],
            cwd=root,
            timeout=timeout,
        )
        return CheckResult(
            name="smoke",
            ok=rc == 0,
            detail=f"powershell {smoke.relative_to(root)} rc={rc}",
            evidence={"cmd": f"powershell -File {smoke}", "output_tail": out[-1500:]},
        )

    if smoke.suffix in {".js", ".mjs", ".ts"}:
        cmd = (
            ["npx", "--yes", "tsx", str(smoke)]
            if smoke.suffix == ".ts"
            else ["node", str(smoke)]
        )
        rc, out = _run(cmd, cwd=root, timeout=timeout)
        return CheckResult(
            name="smoke",
            ok=rc == 0,
            detail=f"{'tsx' if smoke.suffix == '.ts' else 'node'} {smoke.name} rc={rc}",
            evidence={"cmd": " ".join(cmd), "output_tail": out[-1500:]},
        )

    return CheckResult(name="smoke", ok=False, detail=f"unsupported smoke {smoke}")


def _ports_from_readme(root: Path) -> list[int]:
    ports: list[int] = []
    for name in ("README.md", "readme.md", "dev.sh", "dev.bat", "package.json"):
        p = root / name
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in re.finditer(r"localhost:(\d{2,5})|127\.0\.0\.1:(\d{2,5})|:(\d{4,5})\b", text):
            g = next(x for x in m.groups() if x)
            try:
                port = int(g)
            except ValueError:
                continue
            if 1024 <= port <= 65535 and port not in ports:
                ports.append(port)
    return ports[:6]


def _port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.4):
            return True
    except OSError:
        return False


def check_http_health(root: Path, *, ui_surface: str, timeout: int = 8) -> CheckResult:
    """If a server is already listening (agent left it up), probe it. Non-fatal if none."""
    ports = _ports_from_readme(root)
    if not ports and ui_surface in {"api_only", "react_spa", "dashboard_charts", "mobile_web"}:
        ports = [3000, 5173, 8000, 8080, 5000]
    listening = [p for p in ports if _port_open(p)]
    if not listening:
        # Not a hard failure — demos may be CLI-only or stopped after smoke
        return CheckResult(
            name="http_health",
            ok=True,
            detail="no live server (skipped; ok for cli/static)",
            evidence={"ports_checked": ports, "listening": []},
        )
    ok_any = False
    bodies: dict[str, Any] = {}
    for port in listening:
        for path in ("/health", "/api/health", "/", "/index.html"):
            url = f"http://127.0.0.1:{port}{path}"
            try:
                with urllib.request.urlopen(url, timeout=timeout) as resp:
                    code = getattr(resp, "status", 200)
                    if 200 <= int(code) < 500:
                        ok_any = True
                        bodies[url] = code
                        break
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                bodies[url] = str(exc)[:120]
        if ok_any:
            break
    return CheckResult(
        name="http_health",
        ok=ok_any,
        detail=f"listening={listening} probed_ok={ok_any}",
        evidence={"listening": listening, "probes": bodies},
    )


def check_not_stub(root: Path) -> CheckResult:
    """Reject near-empty stubs / TODO-only repos."""
    try:
        files = [p for p in root.rglob("*") if p.is_file()]
    except OSError:
        files = []
    skip = {"node_modules", ".git", "dist", "build", "__pycache__", ".venv", "venv", "target"}
    files = [p for p in files if not any(s in p.parts for s in skip)]
    total_bytes = 0
    todo_hits = 0
    for p in files[:200]:
        try:
            data = p.read_bytes()
        except OSError:
            continue
        total_bytes += len(data)
        if p.suffix.lower() in {".py", ".ts", ".tsx", ".js", ".go", ".rs", ".cs", ".java", ".cpp", ".md"}:
            text = data.decode("utf-8", errors="ignore")
            todo_hits += len(re.findall(r"\bTODO\b|\bFIXME\b|NotImplemented|pass\s*#\s*stub", text))
    ok = len(files) >= 4 and total_bytes >= 400
    if todo_hits > 40 and total_bytes < 8000:
        ok = False
    return CheckResult(
        name="not_stub",
        ok=ok,
        detail=f"files={len(files)} bytes={total_bytes} todoish={todo_hits}",
        evidence={"files": len(files), "bytes": total_bytes, "todoish": todo_hits},
    )


def write_report(report: ValidateReport) -> Path:
    ensure_pipeline_dirs()
    VALIDATE_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.\-]+", "_", report.task_key or "unknown")
    path = VALIDATE_DIR / f"{safe}.json"
    path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return path


def export_synthetic_manifest(report: ValidateReport, root: Path | None) -> Path | None:
    """Record validated demo as a synthetic-data inventory row (scale tracking)."""
    if not report.ok or root is None:
        return None
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.\-]+", "_", report.task_key or "unknown")
    seed_check = next((c for c in report.checks if c.name == "synthetic_seed"), None)
    row = {
        "task_key": report.task_key,
        "root": str(root),
        "language": report.language_runtime,
        "ui_surface": report.ui_surface,
        "validated_at": report.finished_at,
        "seed_files": (seed_check.evidence.get("files") if seed_check else []) or [],
        "smoke_ran": report.smoke_ran,
    }
    path = SYNTHETIC_DIR / f"{safe}.json"
    path.write_text(json.dumps(row, indent=2), encoding="utf-8")
    # append to index
    index = SYNTHETIC_DIR / "index.jsonl"
    with index.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def validate_task(
    *,
    task_key: str,
    workdir: str,
    language_runtime: str = "python",
    ui_surface: str = "static_html",
    run_smoke: bool = True,
    require_seed: bool = True,
    require_http_if_live: bool = True,
    smoke_timeout: int = 120,
) -> ValidateReport:
    started = _utc()
    root = resolve_task_root(workdir)
    report = ValidateReport(
        task_key=task_key,
        workdir=workdir,
        resolved_root=str(root) if root else None,
        language_runtime=language_runtime,
        ui_surface=ui_surface,
        ok=False,
        started_at=started,
    )
    if root is None:
        report.checks.append(
            CheckResult(
                name="resolve_root",
                ok=False,
                detail=f"no demo found for workdir={workdir} under experiments/ or harness/chakra/",
            )
        )
        report.error = "workdir_missing"
        report.finished_at = _utc()
        write_report(report)
        return report

    report.checks.append(
        CheckResult(name="resolve_root", ok=True, detail=str(root), evidence={"root": str(root)})
    )
    report.checks.append(check_structure(root))
    report.checks.append(check_not_stub(root))
    report.checks.append(check_language_lock(root, language_runtime))
    seed = check_synthetic_seed(root)
    if not require_seed:
        seed = CheckResult(name="synthetic_seed", ok=True, detail=seed.detail + " (optional)", evidence=seed.evidence)
    report.checks.append(seed)

    if run_smoke:
        smoke = check_smoke(root, timeout=smoke_timeout)
        report.checks.append(smoke)
        report.smoke_ran = True
    else:
        report.checks.append(CheckResult(name="smoke", ok=True, detail="skipped"))

    http = check_http_health(root, ui_surface=ui_surface)
    if not require_http_if_live:
        http = CheckResult(name="http_health", ok=True, detail=http.detail + " (optional)", evidence=http.evidence)
    report.checks.append(http)
    report.http_checked = True

    # Required gates
    required = {"resolve_root", "structure", "not_stub", "language_lock", "smoke"}
    if require_seed:
        required.add("synthetic_seed")
    report.ok = all(c.ok for c in report.checks if c.name in required)
    # http only required when a server was actually listening
    http_c = next((c for c in report.checks if c.name == "http_health"), None)
    if http_c and http_c.evidence.get("listening") and not http_c.ok:
        report.ok = False

    if not report.ok:
        failed = [c.name for c in report.checks if not c.ok]
        report.error = "validate_failed:" + ",".join(failed)

    report.finished_at = _utc()
    write_report(report)
    export_synthetic_manifest(report, root)
    return report


def validate_queue_item(item: Any, **kwargs: Any) -> ValidateReport:
    return validate_task(
        task_key=getattr(item, "task_key", ""),
        workdir=getattr(item, "workdir", ""),
        language_runtime=getattr(item, "language_runtime", "python"),
        ui_surface=getattr(item, "ui_surface", "static_html"),
        **kwargs,
    )


def format_report(report: ValidateReport) -> str:
    lines = [
        f"VALIDATE {report.task_key} {'PASS' if report.ok else 'FAIL'}",
        f"  root: {report.resolved_root or '(missing)'}",
        f"  lang: {report.language_runtime}  ui: {report.ui_surface}",
    ]
    for c in report.checks:
        mark = "OK" if c.ok else "FAIL"
        lines.append(f"  [{mark}] {c.name}: {c.detail}")
    if report.error:
        lines.append(f"  error: {report.error}")
    return "\n".join(lines)
