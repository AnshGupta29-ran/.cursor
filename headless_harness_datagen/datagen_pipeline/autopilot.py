"""One-command autopilot: expand (optional) -> run every pending task via main.py.

No manual mark-done / paste loop. Crash-safe via checkpoint.json.
Mid-run recovery:
  - Retries timeouts / gRPC stalls / validate fails (does not skip after 1 long fail)
  - Continues from existing workdir on retry instead of restarting from scratch
  - Optional end-of-queue pass over tasks that failed this run

Usage:
  # Terminal A - Chakra gRPC
  cd harness/chakra && bun run dev:grpc

  # Terminal B - full unattended run (base 121 + optional 5k variants)
  python -m datagen_pipeline run-autopilot --base-only --model kimi3
  python -m datagen_pipeline run-autopilot --expand-first 45 --model kimi3
"""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

from datagen_dims.budgets import budget_for
from datagen_pipeline.checkpoint import CheckpointStore
from datagen_pipeline.expand import expand_categories
from datagen_pipeline.langfuse_sink import LangfuseSink
from datagen_pipeline.paths import ROOT
from datagen_pipeline.prompts import write_next_prompt
from datagen_pipeline.queue import QueueItem, build_queue, write_manifest


def _configure_stdio() -> None:
    """Prevent Windows cp1252 UnicodeEncodeError on pipeline prints."""
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


def _grpc_reachable(host: str = "127.0.0.1", port: int = 50051, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _require_grpc_or_exit() -> None:
    host = os.getenv("CHAKRA_GRPC_HOST") or os.getenv("GRPC_HOST") or "127.0.0.1"
    port = int(os.getenv("CHAKRA_GRPC_PORT") or os.getenv("GRPC_PORT") or "50051")
    if _grpc_reachable(host, port):
        print(f"Chakra gRPC OK at {host}:{port}", flush=True)
        return
    print(
        f"FATAL: Chakra gRPC not reachable at {host}:{port}.\n"
        "Start it first in another terminal:\n"
        "  cd harness/chakra\n"
        "  bun run dev:grpc\n"
        "Then re-run autopilot. Refusing to burn tokens on a dead backend.",
        flush=True,
    )
    raise SystemExit(2)

TRANSIENT_RE = re.compile(
    r"502|503|504|Bad Gateway|timeout|temporar|connection reset|fetch failed|"
    r"API Error|gRPC|Exception iterating|stream error|UNAVAILABLE|"
    r"wall_clock|progress_timeout|inactivity|stall|denied_loop|denial_loop|"
    r"write_starvation|no_forward_progress|"
    r"upstream unavailable|model_upstream_503|model_upstream_timeout|api_timeout",
    re.I,
)

_COMPILED_LANGS = frozenset({"cpp", "c", "csharp", "c#", "rust", "go", "java", "kotlin"})

TERMINATION_RE = re.compile(
    r"Termination:\s*(\S+)|Pipeline did not complete \(([^)]+)\)|gRPC stream error",
    re.I,
)
TURNS_RE = re.compile(r"Backend turns:\s*(\d+)", re.I)
COMPLETED_RE = re.compile(r"Completed:\s*(True|False)", re.I)


def _scrape_workdir_tokens(workdir: str) -> tuple[int | None, int | None, int | None]:
    """Best-effort token/tool totals from experiment logs under workdir."""
    root = ROOT / "experiments" / workdir
    if not root.is_dir():
        alt = Path(workdir)
        root = alt if alt.is_dir() else ROOT / workdir
    if not root.is_dir():
        return None, None, None

    tin = tout = tools = 0
    hits = 0
    for path in list(root.rglob("*.jsonl"))[:40]:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line or line[0] != "{":
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if not isinstance(row, dict):
                continue
            usage = row.get("usage") if isinstance(row.get("usage"), dict) else None
            if usage is None and isinstance(row.get("message"), dict):
                usage = (
                    row["message"].get("usage")
                    if isinstance(row["message"].get("usage"), dict)
                    else None
                )
            if usage:
                i = int(
                    usage.get("input_tokens")
                    or usage.get("prompt_tokens")
                    or usage.get("input")
                    or 0
                )
                o = int(
                    usage.get("output_tokens")
                    or usage.get("completion_tokens")
                    or usage.get("output")
                    or 0
                )
                i += int(usage.get("cache_read_input_tokens") or 0)
                i += int(usage.get("cache_creation_input_tokens") or 0)
                if i or o:
                    tin += i
                    tout += o
                    hits += 1
            if row.get("type") in {"tool_use", "tool_result", "tool_call"} or row.get(
                "name"
            ) in {
                "Bash",
                "Write",
                "Edit",
                "Read",
            }:
                tools += 1
    if hits == 0 and tin == 0 and tout == 0:
        return None, None, (tools or None)
    return tin or None, tout or None, (tools or None)


def _workdir_root(item: QueueItem) -> Path:
    p = ROOT / "experiments" / item.workdir
    if p.is_dir():
        return p
    alt = Path(item.workdir)
    return alt if alt.is_dir() else p


def _print_demo_howto(item: QueueItem) -> None:
    """Print workdir + run URL/CLI so operators can verify the shipped demo."""
    root = _workdir_root(item)
    readme = root / "README.md"
    print(f"[{item.task_key}] demo workdir: {root}", flush=True)
    if not readme.is_file():
        return
    try:
        text = readme.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return
    urls = re.findall(
        r"https?://(?:localhost|127\.0\.0\.1)(?::\d+)?(?:/[\w./-]*)?",
        text,
        flags=re.I,
    )
    if urls:
        print(f"[{item.task_key}] open / run at: {urls[0]}", flush=True)
    elif re.search(r"CLI only|no browser", text, re.I):
        print(
            f"[{item.task_key}] platform: CLI — see README Quick start in {readme}",
            flush=True,
        )
    smoke = root / "scripts" / "smoke.py"
    if smoke.is_file():
        print(f"[{item.task_key}] smoke: python {smoke}", flush=True)


def _workdir_has_code(item: QueueItem) -> bool:
    root = _workdir_root(item)
    if not root.is_dir():
        return False
    skip = {".git", "node_modules", "bin", "obj", "target", "__pycache__", ".venv"}
    n = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip for part in path.parts):
            continue
        if path.suffix.lower() in {
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
            ".html",
            ".css",
            ".ps1",
            ".sh",
            ".bat",
            ".md",
            ".json",
            ".toml",
            ".yml",
            ".yaml",
        }:
            n += 1
            if n >= 3:
                return True
    return n >= 1


def _workdir_looks_built(item: QueueItem) -> bool:
    """True when the workdir is a shippable demo (README + smoke + seed + source)."""
    from controller.ship_gate import evaluate_ship_gate

    root = _workdir_root(item)
    status = evaluate_ship_gate(
        root,
        complexity=item.complexity,
        language=item.language_runtime,
    )
    return status.ready


def _workdir_has_source(item: QueueItem) -> bool:
    """True when at least one real source file exists (not markdown/policy)."""
    root = _workdir_root(item)
    if not root.is_dir():
        return False
    skip = {".git", "node_modules", "bin", "obj", "target", "__pycache__", ".venv"}
    code_exts = {
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
    for path in root.rglob("*"):
        if path.is_file() and not any(part in skip for part in path.parts):
            if path.suffix.lower() in code_exts:
                return True
    return False


def _kill_common_demo_ports() -> None:
    """Best-effort free ports left by prior demos (Windows)."""
    if sys.platform != "win32":
        return
    ports = (3000, 5000, 5055, 5173, 8000, 8080, 8765)
    for port in ports:
        try:
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"$c=Get-NetTCPConnection -LocalPort {port} -State Listen "
                    f"-ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; "
                    f"foreach($p in $c){{ if($p){{ Stop-Process -Id $p -Force -ErrorAction SilentlyContinue }}}}",
                ],
                capture_output=True,
                timeout=15,
            )
        except Exception:
            pass


def _parse_run_output(text: str) -> dict[str, str | int | bool | None]:
    term = None
    m = TERMINATION_RE.search(text or "")
    if m:
        term = (m.group(1) or m.group(2) or "grpc_stream_error").strip()
    turns = None
    mt = TURNS_RE.search(text or "")
    if mt:
        turns = int(mt.group(1))
    completed = None
    mc = COMPLETED_RE.search(text or "")
    if mc:
        completed = mc.group(1).lower() == "true"
    return {"termination": term, "turns": turns, "completed": completed}


def _is_retryable(detail: str, *, elapsed: float, turns: int | None) -> bool:
    """Decide whether another attempt is worth it (never skip after one long stall)."""
    d = detail or ""
    if TRANSIENT_RE.search(d):
        return True
    if turns is not None and turns == 0:
        return True  # gRPC hung with no work - always retry
    if elapsed < 180:
        return True  # fast fail
    # Non-zero exit without a clear permanent reason - retry while attempts remain
    if d.startswith("exit=") or d.startswith("validate_failed"):
        return True
    return False


def _skip_agent_verification(args: object) -> bool:
    """Build-first autopilot validates later; do not inline the 2k verification bootstrap."""
    return bool(getattr(args, "skip_verification", False)) or bool(
        getattr(args, "defer_validate", True)
    )


def _objective_for(
    item: QueueItem,
    *,
    attempt: int,
    repair_hint: str | None = None,
) -> str:
    base = (
        f"Implement {item.task_key}: {item.title}. "
        f"Honor language={item.language_runtime}. Full working demo required."
    )
    if repair_hint:
        return (
            f"REPAIR {item.task_key}: previous validate/run failed with: {repair_hint[:500]}. "
            f"Continue in the EXISTING workdir - do not restart from scratch. "
            f"Fix smoke/seed/build until green, then print DONE {item.task_key}. "
            f"Language lock remains {item.language_runtime}."
        )
    # Sticky retries start at attempt 1 again; still CONTINUE if source exists.
    if _workdir_has_source(item) or (attempt > 1 and _workdir_has_code(item)):
        return (
            f"CONTINUE {item.task_key}: {item.title}. "
            f"Workdir already has code - finish the demo, do not rewrite from zero. "
            f"Honor language={item.language_runtime}. Ship smoke + seed, then DONE."
        )
    return base


def _run_main_streamed(
    cmd: list[str],
    *,
    cwd: str,
    env: dict[str, str],
    log_path: Path,
) -> tuple[int, str]:
    """Run main.py with live stdout and a disk log (no RAM capture of the whole run)."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    tail: list[str] = []
    with log_path.open("w", encoding="utf-8", errors="replace") as logf:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            logf.write(line)
            tail.append(line)
            if len(tail) > 4000:
                del tail[:2000]
        rc = proc.wait()
    return rc, "".join(tail)


def run_one(
    item: QueueItem,
    *,
    model: str,
    skip_verification: bool,
    max_retries: int,
    dry_run: bool,
    repair_hint: str | None = None,
    langfuse: LangfuseSink | None = None,
    langfuse_trace: object | None = None,
) -> tuple[bool, str]:
    bud = budget_for(item.complexity)
    cx = (item.complexity or "medium").lower()
    lang = (item.language_runtime or "").strip().lower()
    # Per-band turn floors. Compiled stacks (rust/cpp/go/java/csharp) need more
    # turns for scaffold + build fixes + smoke/seed polish.
    turn_floor = {"low": 160, "medium": 260, "hard": 360}.get(cx, 260)
    if lang in _COMPILED_LANGS:
        turn_floor += {"low": 40, "medium": 120, "hard": 140}.get(cx, 80)
    max_turns = max(int(bud["max_turns"]), turn_floor)
    max_decisions = max(int(bud["max_decisions"]), turn_floor)

    wall_min = float(bud["wall_clock_timeout_minutes"])
    prog_min = float(bud["progress_timeout_minutes"])
    if cx == "low":
        wall_min = max(wall_min, 90.0)
        prog_min = max(prog_min, 40.0)
    elif cx == "medium":
        wall_min = max(wall_min, 130.0)
        prog_min = max(prog_min, 55.0)
    else:
        wall_min = max(wall_min, 170.0)
        prog_min = max(prog_min, 70.0)
    if lang in _COMPILED_LANGS:
        wall_min += 25.0
        prog_min += 15.0

    env = os.environ.copy()
    env["OPENAI_MODEL"] = model
    # Force Plan/GP/Explore onto the same proxy model. Agents often pass
    # model="sonnet" which resolves to Claude and returns 0 tokens on OpenAI.
    env["CLAUDE_CODE_SUBAGENT_MODEL"] = model
    env["DATAGEN_PIPELINE_MODE"] = "1"
    env["HARNESS_COMPLEXITY"] = (item.complexity or "medium").strip().lower()
    env["HARNESS_LANGUAGE"] = (item.language_runtime or "").strip().lower()
    env["HARNESS_WALL_CLOCK_TIMEOUT_MINUTES"] = str(wall_min)
    env["HARNESS_PROGRESS_TIMEOUT_MINUTES"] = str(prog_min)
    env["HARNESS_MAX_REPAIR_ITERATIONS"] = str(bud["max_repair_iterations"])
    # Allow a few proxy 503 / GPT first-token timeouts inside one conversation.
    # Threshold 1 treated "API Error: The operation timed out" as fatal and
    # stuck the queue on the same task (GPT and kimi).
    env["HARNESS_REPEATED_FAILURE_THRESHOLD"] = "16"
    env["HARNESS_MODEL_503_THRESHOLD"] = "3"
    # Stream idle cancels used to need 10×6min ≈ 1h before fail-fast.
    env["HARNESS_MODEL_TIMEOUT_THRESHOLD"] = "4"
    # Idle gRPC wait must exceed TensorStudio's ~300s first-token timeout so we
    # receive DONE "API Error: The operation timed out" instead of cancelling
    # a live request (180s caused CANCELLED / hung streams). 1800s hung dead ones.
    env["HARNESS_TURN_TIMEOUT"] = "360"
    env["HARNESS_STAGNATION_GRACE_CYCLES"] = "0"
    # gpt finishes a turn after a few tools; keep stall high so writes can finish.
    env["HARNESS_STALL_CYCLES"] = "24"
    env["HARNESS_MAX_RECOVERY_ATTEMPTS"] = "40"
    env["HARNESS_DENIAL_LOOP_THRESHOLD"] = "8"
    # Avoid Windows cp1252 UnicodeEncodeError on child prints (arrows etc.).
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")

    last_err = ""
    for attempt in range(1, max_retries + 1):
        _kill_common_demo_ports()
        write_next_prompt(item, remaining=0, model=model)
        objective = _objective_for(item, attempt=attempt, repair_hint=repair_hint)
        attempt_max_turns = max_turns
        attempt_max_decisions = max_decisions
        if attempt > 1 and _workdir_has_code(item):
            env["HARNESS_WALL_CLOCK_TIMEOUT_MINUTES"] = str(wall_min + 20)
            attempt_max_turns += 40
            attempt_max_decisions += 40

        cmd = [
            sys.executable,
            str(ROOT / "main.py"),
            objective,
            "--platform-prompt-file",
            item.platform_prompt,
            "--workdir",
            item.workdir,
            "--max-repair-iterations",
            str(bud["max_repair_iterations"]),
            "--max-turns",
            str(attempt_max_turns),
            "--max-decisions",
            str(attempt_max_decisions),
        ]
        if skip_verification:
            cmd.append("--skip-verification")
        cmd.extend(["--model", model])

        if dry_run:
            print("DRY", " ".join(cmd[:6]), "...", flush=True)
            return False, "dry-run"

        print(
            f"[{item.task_key}] attempt {attempt}/{max_retries} "
            f"lang={item.language_runtime} cx={item.complexity} "
            f"max_turns={attempt_max_turns} wall={env['HARNESS_WALL_CLOCK_TIMEOUT_MINUTES']}m"
            f"{' REPAIR' if repair_hint else ''}"
            f"{' CONTINUE' if attempt > 1 and not repair_hint else ''}",
            flush=True,
        )
        t0 = time.time()
        log_path = ROOT / "logs" / "autopilot" / f"{item.task_key.replace(':', '_')}_attempt{attempt}.log"
        if langfuse is not None and langfuse_trace is not None:
            langfuse.start_live_mirror(
                task_trace=langfuse_trace,
                logs_root=ROOT / "logs",
                task_key=item.task_key,
                model=model,
            )
        try:
            rc, combined = _run_main_streamed(cmd, cwd=str(ROOT), env=env, log_path=log_path)
            elapsed = time.time() - t0
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
            print(f"[{item.task_key}] exception: {last_err}", flush=True)
            if attempt < max_retries:
                time.sleep(min(15 * attempt, 60))
                continue
            return False, last_err
        finally:
            if langfuse is not None:
                langfuse.stop_live_mirror()

        meta = _parse_run_output(combined)
        term = str(meta.get("termination") or "")
        turns = meta.get("turns")
        turns_i = int(turns) if isinstance(turns, int) else None

        if rc == 0 and meta.get("completed") is False:
            # Harness exited 0 but agent never finished — treat as incomplete.
            print(
                f"[{item.task_key}] exit=0 but Completed=False - treating as fail",
                flush=True,
            )
            last_err = f"exit=0:incomplete:turns={turns_i}"
            if attempt < max_retries:
                time.sleep(8)
                continue
            return False, last_err

        if rc == 0:
            print(f"[{item.task_key}] OK in {elapsed:.0f}s", flush=True)
            return True, f"ok:{elapsed:.0f}s"

        # Only advance without a completion marker if the workdir is actually
        # a shippable demo. Thin leftovers must CONTINUE, not stamp BUILT.
        if skip_verification and _workdir_looks_built(item) and term in {
            "max_turns",
            "max_decisions",
            "no_forward_progress",
        }:
            print(
                f"[{item.task_key}] skip-verification: shippable workdir after "
                f"{term} - treating as built",
                flush=True,
            )
            return True, f"built_without_marker:{term}:turns={turns_i}"

        last_err = f"exit={rc}:{term}" if term else f"exit={rc}"
        if turns_i is not None:
            last_err += f":turns={turns_i}"

        print(f"[{item.task_key}] fail {last_err} ({elapsed:.0f}s) log={log_path}", flush=True)

        timeout_only = bool(
            re.search(r"model_upstream_timeout|api_timeout", last_err, re.I)
        )
        if timeout_only and attempt >= 2:
            print(
                f"[{item.task_key}] proxy first-token timeout twice - "
                "not burning more 5-min turns on this task",
                flush=True,
            )
            return False, last_err

        # Do NOT mark incomplete wall-clock kills as built — that skips unfinished
        # demos. Stay on the task and CONTINUE the existing workdir.

        if attempt < max_retries and _is_retryable(
            last_err + " " + (combined[-2000:] if combined else ""),
            elapsed=elapsed,
            turns=turns_i,
        ):
            is_503 = bool(
                re.search(
                    r"503|upstream unavailable|model_upstream_503",
                    last_err + " " + (combined[-1500:] if combined else ""),
                    re.I,
                )
            )
            if is_503:
                wait = min(30 * attempt, 90)
                print(
                    f"[{item.task_key}] model/proxy 503 - backoff {wait}s then CONTINUE same task",
                    flush=True,
                )
            elif turns_i == 0 or TRANSIENT_RE.search(term or last_err):
                wait = 8
                print(
                    f"[{item.task_key}] mid-run recovery - retry in {wait}s "
                    f"(will CONTINUE existing workdir if present)",
                    flush=True,
                )
            else:
                wait = min(15 * attempt, 45)
                print(
                    f"[{item.task_key}] mid-run recovery - retry in {wait}s "
                    f"(will CONTINUE existing workdir if present)",
                    flush=True,
                )
            time.sleep(wait)
            continue
        return False, last_err

    return False, last_err or "max_retries"


def _record_stats(
    item: QueueItem,
    *,
    model: str,
    elapsed: float,
    status: str,
) -> None:
    try:
        from prompt_stats.datagen_views import record_autopilot_task

        tin, tout, tools = _scrape_workdir_tokens(item.workdir)
        record_autopilot_task(
            task_key=item.task_key,
            title=item.title,
            category=item.category,
            model=str(model),
            workdir=item.workdir,
            platform_prompt=item.platform_prompt,
            dimensions={
                "language_runtime": item.language_runtime,
                "ui_surface": item.ui_surface,
                "persistence": item.persistence,
                "complexity": item.complexity,
                "variant": item.variant,
            },
            input_tokens=tin,
            output_tokens=tout,
            runtime_seconds=elapsed,
            tool_calls=tools,
            status=status,
            run_id=os.getenv("DATAGEN_RUN_ID")
            or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[{item.task_key}] prompt_stats record skipped: {exc}", flush=True)


def _validate_item(item: QueueItem, args) -> tuple[bool, str]:
    from datagen_pipeline.validate import format_report, validate_queue_item

    report = validate_queue_item(
        item,
        run_smoke=not getattr(args, "skip_smoke", False),
        require_seed=not getattr(args, "skip_seed", False),
        smoke_timeout=int(getattr(args, "smoke_timeout", 120) or 120),
    )
    print(format_report(report), flush=True)
    if report.ok:
        return True, "validated"
    return False, report.error or "validate_failed"


def _process_item(
    item: QueueItem,
    *,
    args,
    store: CheckpointStore,
    lf: LangfuseSink,
    index: int,
    total: int,
) -> str:
    """Run one queue item with validate + repair. Returns status: done|failed|skipped."""
    print("=" * 72, flush=True)
    print(f"TASK {index}/{total} {item.task_key} - {item.title}", flush=True)

    # Before spending wall-clock: ensure gRPC is alive (recover briefly if flapping).
    if not getattr(args, "dry_run", False):
        host = os.getenv("CHAKRA_GRPC_HOST") or os.getenv("GRPC_HOST") or "127.0.0.1"
        port = int(os.getenv("CHAKRA_GRPC_PORT") or os.getenv("GRPC_PORT") or "50051")
        if not _grpc_reachable(host, port):
            print(
                f"[{item.task_key}] gRPC down at {host}:{port} - waiting up to 60s...",
                flush=True,
            )
            deadline = time.time() + 60
            while time.time() < deadline and not _grpc_reachable(host, port):
                time.sleep(3)
            if not _grpc_reachable(host, port):
                store.mark_failed(
                    item.task_key,
                    f"grpc_unreachable:{host}:{port}",
                    mode="autopilot",
                )
                print(
                    f"[{item.task_key}] FAIL grpc unreachable - skip to next "
                    "(will retry on failed-pass / next run)",
                    flush=True,
                )
                return "failed"

    # Already shippable (e.g. smoke/README fixed offline) — do not burn wall clock.
    defer = bool(getattr(args, "defer_validate", True))
    if (
        not getattr(args, "dry_run", False)
        and defer
        and _workdir_looks_built(item)
    ):
        store.mark_built(
            item.task_key,
            category=item.category,
            workdir=item.workdir,
            platform_prompt=item.platform_prompt,
            mode="autopilot",
            language=item.language_runtime,
            detail="already_shippable",
            defer_validate=True,
        )
        print(
            f"[{item.task_key}] BUILT (workdir already shippable) - moving to next task",
            flush=True,
        )
        _print_demo_howto(item)
        return "built"

    store.mark_running(
        item.task_key,
        category=item.category,
        workdir=item.workdir,
        platform_prompt=item.platform_prompt,
        mode="autopilot",
        language=item.language_runtime,
    )
    tr = lf.start_task_trace(
        task_key=item.task_key,
        metadata={
            "category": item.category,
            "language": item.language_runtime,
            "complexity": item.complexity,
            "mode": "autopilot",
        },
    )
    t_task = time.time()
    success, detail = run_one(
        item,
        model=str(args.model),
        skip_verification=_skip_agent_verification(args),
        max_retries=int(args.max_retries),
        dry_run=bool(args.dry_run),
        langfuse=lf,
        langfuse_trace=tr,
    )
    elapsed = time.time() - t_task
    m_elapsed = re.search(r"ok:(\d+(?:\.\d+)?)s", detail or "")
    if m_elapsed:
        try:
            elapsed = float(m_elapsed.group(1))
        except ValueError:
            pass

    if args.dry_run:
        store.mark_skipped(item.task_key, "dry-run")
        lf.end_ok(tr, output={"status": "skipped", "detail": detail})
        return "skipped"

    status = "failed"
    if success:
        lf.attach_run_artifacts(tr, task_key=item.task_key, workdir=item.workdir)
        defer = bool(getattr(args, "defer_validate", True))
        require_validate = not getattr(args, "skip_validate", False)

        # Build-first mode: only advance when agent truly finished AND shipped code.
        if defer or not require_validate:
            if not _workdir_looks_built(item):
                print(
                    f"[{item.task_key}] agent reported OK but workdir thin - "
                    "NOT marking built; will retry",
                    flush=True,
                )
                store.upsert(
                    item.task_key,
                    status="pending",
                    error="incomplete_workdir_after_ok",
                )
                lf.end_error(tr, "incomplete_workdir_after_ok")
                _record_stats(item, model=str(args.model), elapsed=elapsed, status="failed")
                return "failed"
            store.mark_built(
                item.task_key,
                note=detail,
                mode="autopilot",
                defer_validate=True,
            )
            lf.end_ok(
                tr,
                output={
                    "status": "built",
                    "detail": detail,
                    "validated": False,
                    "deferred_validate": True,
                },
            )
            print(
                f"[{item.task_key}] BUILT - validate/repair deferred; moving to next task",
                flush=True,
            )
            _print_demo_howto(item)
            status = "built"
        else:
            validated_ok = True
            val_detail = detail
            if require_validate:
                validated_ok, val_detail = _validate_item(item, args)
                if not validated_ok:
                    print(
                        f"[{item.task_key}] VALIDATE FAIL - mid-run repair attempt...",
                        flush=True,
                    )
                    repair_ok, repair_detail = run_one(
                        item,
                        model=str(args.model),
                        skip_verification=_skip_agent_verification(args),
                        max_retries=max(2, min(int(args.max_retries), 3)),
                        dry_run=False,
                        repair_hint=val_detail,
                    )
                    elapsed = time.time() - t_task
                    if repair_ok:
                        validated_ok, val_detail = _validate_item(item, args)
                        detail = f"{detail};repair:{repair_detail};{val_detail}"
                    else:
                        detail = (
                            f"validate_failed:{val_detail};repair_failed:{repair_detail}"
                        )
                        validated_ok = False

            if validated_ok:
                store.mark_done(
                    item.task_key,
                    note=detail,
                    mode="autopilot",
                    validated=require_validate,
                )
                lf.end_ok(
                    tr,
                    output={
                        "status": "done",
                        "detail": detail,
                        "validated": require_validate,
                    },
                )
                status = "done"
            else:
                store.mark_failed(item.task_key, detail, mode="validate")
                lf.end_error(tr, detail)
                status = "failed"
    else:
        lf.attach_run_artifacts(tr, task_key=item.task_key, workdir=item.workdir)
        store.mark_failed(item.task_key, detail, mode="autopilot")
        lf.end_error(tr, detail)
        status = "failed"

    _record_stats(item, model=str(args.model), elapsed=elapsed, status=status)
    return status


def _validate_built_pass(
    items: list[QueueItem],
    *,
    args,
    store: CheckpointStore,
    lf: LangfuseSink,
) -> tuple[int, list[str]]:
    """After build queue: validate built tasks; optionally one repair if --repair-built."""
    built = [it for it in items if store.status(it.task_key) == "built"]
    if not built:
        return 0, []
    do_repair = bool(getattr(args, "repair_built", False))
    print("=" * 72, flush=True)
    print(
        f"VALIDATE-PASS: {len(built)} built task(s) "
        f"(repair={'ON' if do_repair else 'OFF - mark failed on validate miss'})",
        flush=True,
    )
    ok_n = 0
    failed: list[str] = []
    for j, item in enumerate(built, 1):
        print("-" * 64, flush=True)
        print(f"VALIDATE {j}/{len(built)} {item.task_key}", flush=True)
        validated_ok, val_detail = _validate_item(item, args)
        detail = val_detail
        if not validated_ok and do_repair:
            print(f"[{item.task_key}] repair-built attempt...", flush=True)
            repair_ok, repair_detail = run_one(
                item,
                model=str(args.model),
                skip_verification=_skip_agent_verification(args),
                max_retries=max(2, min(int(args.max_retries), 3)),
                dry_run=False,
                repair_hint=val_detail,
            )
            if repair_ok:
                validated_ok, val_detail = _validate_item(item, args)
                detail = f"repair:{repair_detail};{val_detail}"
            else:
                detail = f"validate_failed:{val_detail};repair_failed:{repair_detail}"
                validated_ok = False
        if validated_ok:
            store.mark_done(
                item.task_key,
                note=detail,
                mode="autopilot",
                validated=True,
            )
            ok_n += 1
            print(f"[{item.task_key}] validated -> done", flush=True)
        else:
            store.mark_failed(item.task_key, detail, mode="validate")
            failed.append(item.task_key)
            print(f"[{item.task_key}] validate still failing", flush=True)
    return ok_n, failed


def run_autopilot(args) -> int:
    _configure_stdio()
    from datagen_pipeline.queue import BIG_RUN_CATEGORIES

    def parse_cats(s: str | None) -> list[str]:
        if not s:
            return list(BIG_RUN_CATEGORIES)
        return [c.strip() for c in s.split(",") if c.strip()]

    def queue_kwargs() -> dict:
        return {
            "categories": parse_cats(getattr(args, "categories", None)),
            "include_expanded": not getattr(args, "base_only", False),
            "skip_already_done": not getattr(args, "force_all", False),
            "force_all": bool(getattr(args, "force_all", False)),
        }

    def pending(items: list[QueueItem], store: CheckpointStore) -> list[QueueItem]:
        out: list[QueueItem] = []
        for it in items:
            st = store.status(it.task_key)
            # built = agent finished; wait for validate-pass (do not rebuild)
            if st in ("done", "skipped", "built"):
                continue
            out.append(it)
        return out

    # Fail fast if Chakra is down (otherwise wall-clock burns with 0 turns).
    if not getattr(args, "dry_run", False):
        _require_grpc_or_exit()

    store = CheckpointStore()
    store.reset_running()

    if getattr(args, "expand_first", 0) and args.expand_first > 0:
        cats = parse_cats(args.categories)
        n = expand_categories(
            cats,
            variants_per_task=args.expand_first,
            quiet=True,
            skip_existing=True,
        )
        print(
            f"Variant PRDs ready: {n} total "
            f"({args.expand_first}/base task, existing files reused)",
            flush=True,
        )
        if args.base_only:
            print(
                "NOTE: --base-only set - variants generated but not queued this run.",
                flush=True,
            )

    items = build_queue(**queue_kwargs())
    write_manifest(items)
    todo = pending(items, store)
    print(
        f"AUTOPILOT queue={len(items)} pending={len(todo)} model={args.model}",
        flush=True,
    )
    print(
        "Requires Chakra gRPC on :50051 (bun run dev:grpc in harness/chakra)",
        flush=True,
    )
    defer = bool(getattr(args, "defer_validate", True))
    print(
        "Mid-run recovery ON: retry timeouts/gRPC; CONTINUE existing workdirs; "
        "end-of-queue failed pass.",
        flush=True,
    )
    print(
        f"Build-first defer_validate={'ON' if defer else 'OFF'} "
        f"(inline repair {'disabled' if defer else 'enabled'}; "
        "validate-pass runs after build queue).",
        flush=True,
    )

    lf = LangfuseSink()
    lf.start_run_session(
        model=str(args.model),
        mode="autopilot",
        meta={
            "pending": len(todo),
            "queue": len(items),
            "base_only": bool(args.base_only),
        },
    )
    failed: list[str] = []
    ok_n = 0
    failed_this_run: list[QueueItem] = []
    sticky_max = int(getattr(args, "sticky_retries", 20) or 20)

    # Sticky queue: do not advance past an incomplete *build* until it succeeds
    # or sticky_max outer attempts are exhausted.
    idx = 0
    sticky_counts: dict[str, int] = {}
    while idx < len(todo):
        item = todo[idx]
        status = _process_item(
            item,
            args=args,
            store=store,
            lf=lf,
            index=idx + 1,
            total=len(todo),
        )
        if status in ("done", "built"):
            ok_n += 1
            sticky_counts.pop(item.task_key, None)
            idx += 1
            continue

        if status == "failed":
            sticky_counts[item.task_key] = sticky_counts.get(item.task_key, 0) + 1
            n_stick = sticky_counts[item.task_key]
            row = store.get(item.task_key) or {}
            err = str(row.get("error") or "")
            transient = bool(
                re.search(
                    r"503|timeout|turns=0|model_upstream|grpc_unreachable",
                    err,
                    re.I,
                )
            )
            # One flaky GPT/proxy task must not freeze the rest of the queue
            # (even if a previous attempt left files in the workdir).
            cap = 1 if re.search(
                r"model_upstream_timeout|api_timeout|write_starvation|"
                r"Bad Gateway|\b502\b|Unable to connect|typo in the url|"
                r"socket connection was closed",
                err,
                re.I,
            ) else (2 if transient else sticky_max)
            if n_stick < cap:
                print(
                    f"[{item.task_key}] STICKY: incomplete - staying on this task "
                    f"({n_stick}/{cap}); not skipping to next.",
                    flush=True,
                )
                store.upsert(item.task_key, status="pending", error=None)
                time.sleep(5)
                continue  # same idx
            print(
                f"[{item.task_key}] STICKY exhausted ({cap}) - "
                "advancing so later tasks still run; retry in failed-pass",
                flush=True,
            )
            if item.task_key not in failed:
                failed.append(item.task_key)
            failed_this_run.append(item)
            if args.stop_on_error:
                print("stop-on-error: exiting; re-run autopilot to resume.", flush=True)
                return 1
            idx += 1
            continue

        # skipped / other
        idx += 1

    # End-of-queue recovery pass: re-try tasks that failed this run (timeouts etc.).
    extra_passes = int(getattr(args, "failed_passes", 1) or 0)
    for pass_i in range(1, extra_passes + 1):
        if not failed_this_run:
            break
        print("=" * 72, flush=True)
        print(
            f"FAILED-PASS {pass_i}/{extra_passes}: retrying {len(failed_this_run)} "
            f"task(s) that failed earlier this run (no skip-and-forget).",
            flush=True,
        )
        again: list[QueueItem] = []
        for j, item in enumerate(failed_this_run, 1):
            # Flip back to pending so mark_running/attempts stay coherent.
            store.upsert(item.task_key, status="pending", error=None)
            status = _process_item(
                item,
                args=args,
                store=store,
                lf=lf,
                index=j,
                total=len(failed_this_run),
            )
            if status in ("done", "built"):
                ok_n += 1
                if item.task_key in failed:
                    failed.remove(item.task_key)
            elif status == "failed":
                again.append(item)
        failed_this_run = again

    # After all builds: validate (and optionally repair) deferred built tasks.
    if defer and not getattr(args, "skip_validate", False):
        v_ok, v_fail = _validate_built_pass(items, args=args, store=store, lf=lf)
        ok_n += v_ok
        for k in v_fail:
            if k not in failed:
                failed.append(k)

    print("=" * 72, flush=True)
    print(
        f"AUTOPILOT finished ok={ok_n} failed={len(failed)} "
        f"built_pending_validate="
        f"{sum(1 for it in items if store.status(it.task_key) == 'built')}",
        flush=True,
    )
    lf.end_run_session(ok=ok_n, failed=len(failed))
    if failed:
        print("Failed keys:", ", ".join(failed[:40]), flush=True)
        print("Re-run the same command to retry failed/pending only.", flush=True)
        return 1
    return 0
