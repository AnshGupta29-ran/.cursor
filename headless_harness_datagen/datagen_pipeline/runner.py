"""Checkpointed pipeline runner.

Modes:
  status       - show queue + checkpoint summary
  next         - write thin CHAKRA_NEXT_TASK.md for first pending item
  mark-done    - mark task_key done (after interactive Chakra DONE)
  mark-failed  - mark failed with error (auto-retry later)
  run-headless - loop: each pending task -> main.py with existing PRD (one at a time)
  expand       - generate variant PRDs toward ~5k
  reset-running / reset-failed

Interactive (Chakra kimi3) loop:
  1) python -m datagen_pipeline next
  2) paste harness/chakra/CHAKRA_NEXT_TASK.md into Chakra
  3) when agent prints DONE ... -> python -m datagen_pipeline mark-done --key ...
  4) repeat from (1)

Never paste all-10 forged files. One PRD per session turn / headless subprocess.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from datagen_pipeline.checkpoint import CheckpointStore
from datagen_pipeline.expand import expand_categories
from datagen_pipeline.langfuse_sink import LangfuseSink
from datagen_pipeline.paths import ROOT, STATUS_PATH, ensure_pipeline_dirs
from datagen_pipeline.prompts import write_next_prompt
from datagen_pipeline.queue import (
    BIG_RUN_CATEGORIES,
    QueueItem,
    build_queue,
    write_manifest,
)

from datagen_dims.budgets import budget_for


def _parse_cats(s: str | None) -> list[str]:
    if not s:
        return list(BIG_RUN_CATEGORIES)
    return [c.strip() for c in s.split(",") if c.strip()]


def _queue_kwargs(args: argparse.Namespace) -> dict:
    return {
        "categories": _parse_cats(getattr(args, "categories", None)),
        "include_expanded": not getattr(args, "base_only", False),
        "skip_already_done": not getattr(args, "force_all", False),
        "force_all": bool(getattr(args, "force_all", False)),
    }


def _pending(items: list[QueueItem], store: CheckpointStore) -> list[QueueItem]:
    out: list[QueueItem] = []
    for it in items:
        st = store.status(it.task_key)
        # built = agent finished; waiting for validate-pass (not a build-queue item)
        if st in ("done", "skipped", "built"):
            continue
        if st == "running":
            # treat as retryable unless --strict
            out.append(it)
            continue
        out.append(it)
    return out


def cmd_status(args: argparse.Namespace) -> int:
    store = CheckpointStore()
    recovered = store.reset_running() if getattr(args, "recover", False) else 0
    items = build_queue(**_queue_kwargs(args))
    write_manifest(items)
    pending = _pending(items, store)
    summary = store.summary()
    langs = sorted({i.language_runtime for i in items})
    lines = [
        "# Datagen pipeline status",
        "",
        f"- queue_size: **{len(items)}**",
        f"- pending_or_retry: **{len(pending)}**",
        f"- languages_in_queue: {', '.join(langs)}",
        f"- checkpoint: `{summary}`",
        f"- recovered_running_to_pending: {recovered}",
        "",
        "## Next 15",
        "",
    ]
    for it in pending[:15]:
        lines.append(
            f"- `{it.task_key}` - {it.title} [{it.language_runtime}/{it.complexity}] -> `{it.workdir}`"
        )
    if pending:
        lines += ["", f"Next key: `{pending[0].task_key}`"]
    text = "\n".join(lines) + "\n"
    ensure_pipeline_dirs()
    STATUS_PATH.write_text(text, encoding="utf-8")
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    store = CheckpointStore()
    items = build_queue(**_queue_kwargs(args))
    pending = _pending(items, store)
    if not pending:
        print("Queue empty - all done/skipped.")
        return 0
    item = pending[0]
    store.mark_running(
        item.task_key,
        category=item.category,
        workdir=item.workdir,
        platform_prompt=item.platform_prompt,
        mode="interactive",
    )
    text = write_next_prompt(item, remaining=max(0, len(pending) - 1), model=args.model)
    print(text)
    print(
        f"\n---\nWrote prompt. After Chakra prints DONE, run:\n"
        f"  python -m datagen_pipeline mark-done --key {item.task_key} --base-only\n",
        flush=True,
    )
    return 0


def cmd_mark_done(args: argparse.Namespace) -> int:
    store = CheckpointStore()
    item = _find_item(args.key, args)
    if not getattr(args, "force", False):
        from datagen_pipeline.validate import format_report, validate_task

        lang = item.language_runtime if item else "python"
        ui = item.ui_surface if item else "static_html"
        workdir = item.workdir if item else args.key.replace(":", "_")
        if item is None:
            # best-effort workdir from checkpoint
            row = store.get(args.key) or {}
            workdir = str(row.get("workdir") or workdir)
            lang = str(row.get("language") or lang)
        report = validate_task(
            task_key=args.key,
            workdir=workdir,
            language_runtime=lang,
            ui_surface=ui,
            run_smoke=not getattr(args, "skip_smoke", False),
            require_seed=not getattr(args, "skip_seed", False),
        )
        print(format_report(report), flush=True)
        if not report.ok:
            store.mark_failed(args.key, report.error or "validate_failed", mode="validate")
            print("Refusing mark-done - validate failed. Fix demo or pass --force.", flush=True)
            return 1

    store.mark_done(
        args.key,
        note=args.note or "",
        validated=True,
        mode="interactive",
    )
    lf = LangfuseSink()
    tr = lf.start_task_trace(
        task_key=args.key,
        metadata={"status": "done", "mode": "interactive", "note": args.note or "", "validated": True},
    )
    lf.end_ok(tr, output={"status": "done", "note": args.note or "", "validated": True})
    print(f"Marked done: {args.key}")
    # auto-write next prompt
    if not args.no_next:
        return cmd_next(args)
    return 0


def _find_item(task_key: str, args: argparse.Namespace):
    items = build_queue(**_queue_kwargs(args))
    for it in items:
        if it.task_key == task_key:
            return it
    # also search including skipped demos
    items = build_queue(
        categories=_parse_cats(getattr(args, "categories", None)),
        include_expanded=not getattr(args, "base_only", False),
        skip_already_done=False,
        force_all=True,
    )
    for it in items:
        if it.task_key == task_key:
            return it
    return None


def cmd_validate(args: argparse.Namespace) -> int:
    from datagen_pipeline.validate import format_report, validate_task

    item = None
    if args.key:
        item = _find_item(args.key, args)
    workdir = args.workdir or (item.workdir if item else None)
    if not workdir:
        print("Need --key or --workdir", flush=True)
        return 2
    report = validate_task(
        task_key=args.key or (item.task_key if item else workdir),
        workdir=workdir,
        language_runtime=args.language
        or (item.language_runtime if item else "python"),
        ui_surface=args.ui or (item.ui_surface if item else "static_html"),
        run_smoke=not args.skip_smoke,
        require_seed=not args.skip_seed,
        smoke_timeout=int(args.smoke_timeout),
    )
    print(format_report(report), flush=True)
    return 0 if report.ok else 1


def cmd_mark_failed(args: argparse.Namespace) -> int:
    store = CheckpointStore()
    store.mark_failed(args.key, args.error or "unspecified")
    lf = LangfuseSink()
    tr = lf.start_task_trace(
        task_key=args.key,
        metadata={"status": "failed", "mode": "interactive"},
    )
    lf.end_error(tr, args.error or "unspecified")
    print(f"Marked failed: {args.key}")
    return 0


def cmd_mark_built(args: argparse.Namespace) -> int:
    """Mark agent build complete; validate deferred (build-first queue)."""
    store = CheckpointStore()
    item = _find_item(args.key, args)
    extra: dict = {"note": args.note or "manual built"}
    if item is not None:
        extra["workdir"] = item.workdir
        extra["platform_prompt"] = item.platform_prompt
    store.mark_built(args.key, **extra)
    print(f"Marked built: {args.key} (validate deferred)")
    return 0


def cmd_run_headless(args: argparse.Namespace) -> int:
    """One main.py subprocess per task; checkpoint after each; resume forever."""
    store = CheckpointStore()
    store.reset_running()
    items = build_queue(**_queue_kwargs(args))
    write_manifest(items)
    lf = LangfuseSink()
    pending = _pending(items, store)
    print(f"Headless queue: {len(pending)} pending / {len(items)} total", flush=True)
    print("Ensure Chakra gRPC is up on :50051", flush=True)

    max_attempts = args.max_attempts
    failed_keys: list[str] = []

    for item in pending:
        st = store.status(item.task_key)
        row = store.get(item.task_key) or {}
        if int(row.get("attempts") or 0) >= max_attempts and st == "failed":
            print(f"SKIP {item.task_key} (max attempts)", flush=True)
            continue

        store.mark_running(
            item.task_key,
            category=item.category,
            workdir=item.workdir,
            platform_prompt=item.platform_prompt,
            mode="headless",
        )
        tr = lf.start_task_trace(
            task_key=item.task_key,
            metadata={
                "category": item.category,
                "workdir": item.workdir,
                "complexity": item.complexity,
                "variant": item.variant,
                "platform_prompt": item.platform_prompt,
            },
        )
        span = lf.span(tr, "main_py")

        bud = budget_for(item.complexity)
        env = os.environ.copy()
        env["HARNESS_WALL_CLOCK_TIMEOUT_MINUTES"] = str(bud["wall_clock_timeout_minutes"])
        env["HARNESS_PROGRESS_TIMEOUT_MINUTES"] = str(bud["progress_timeout_minutes"])
        env["HARNESS_MAX_REPAIR_ITERATIONS"] = str(bud["max_repair_iterations"])
        # Prefer interactive model for TensorStudio when set
        if args.model:
            env["OPENAI_MODEL"] = args.model
            env["CLAUDE_CODE_SUBAGENT_MODEL"] = args.model
        elif env.get("OPENAI_MODEL"):
            env["CLAUDE_CODE_SUBAGENT_MODEL"] = env["OPENAI_MODEL"]

        prompt_text = Path(item.platform_prompt).read_text(encoding="utf-8")
        # Keep objective short for argv: point at file; main.py loads full PRD
        cmd = [
            sys.executable,
            str(ROOT / "main.py"),
            f"Implement the platform PRD for {item.task_key}: {item.title}",
            "--platform-prompt-file",
            item.platform_prompt,
            "--workdir",
            item.workdir,
            "--max-repair-iterations",
            str(bud["max_repair_iterations"]),
            "--max-turns",
            str(bud["max_turns"]),
            "--max-decisions",
            str(bud["max_decisions"]),
        ]
        if args.skip_verification:
            cmd.append("--skip-verification")

        print("=" * 72, flush=True)
        print(f"RUN {item.task_key}  cx={item.complexity}  chars_prd={len(prompt_text)}", flush=True)
        if args.dry_run:
            print(" ".join(cmd), flush=True)
            store.mark_skipped(item.task_key, "dry-run")
            continue

        t0 = time.time()
        try:
            proc = subprocess.run(cmd, cwd=str(ROOT), env=env)
            rc = proc.returncode
        except Exception as exc:  # noqa: BLE001
            rc = 99
            err = str(exc)
            store.mark_failed(item.task_key, err, elapsed_s=time.time() - t0)
            lf.end_error(tr, err)
            failed_keys.append(item.task_key)
            if not args.continue_on_error:
                return 1
            continue

        elapsed = time.time() - t0
        if span:
            try:
                span.end()
            except Exception:
                pass

        if rc == 0:
            from datagen_pipeline.validate import format_report, validate_queue_item

            require_validate = not getattr(args, "skip_validate", False)
            if require_validate:
                report = validate_queue_item(
                    item,
                    run_smoke=not getattr(args, "skip_smoke", False),
                    require_seed=not getattr(args, "skip_seed", False),
                )
                print(format_report(report), flush=True)
                if not report.ok:
                    err = report.error or "validate_failed"
                    store.mark_failed(
                        item.task_key,
                        err,
                        elapsed_s=elapsed,
                        exit_code=rc,
                        mode="validate",
                    )
                    lf.end_error(tr, err)
                    failed_keys.append(item.task_key)
                    print(f"VALIDATE FAIL {item.task_key} {err}", flush=True)
                    if not args.continue_on_error:
                        return 1
                    continue
            store.mark_done(
                item.task_key,
                elapsed_s=elapsed,
                exit_code=0,
                validated=True,
            )
            lf.end_ok(tr, output={"status": "done", "elapsed_s": elapsed, "validated": True})
            print(f"OK {item.task_key} in {elapsed:.0f}s (validated)", flush=True)
        else:
            err = f"exit={rc}"
            store.mark_failed(item.task_key, err, elapsed_s=elapsed, exit_code=rc)
            lf.end_error(tr, err)
            failed_keys.append(item.task_key)
            print(f"FAIL {item.task_key} {err}", flush=True)
            if not args.continue_on_error:
                print("Stopping; re-run to resume from checkpoint.", flush=True)
                return 1

    print("Headless pass finished.", flush=True)
    if failed_keys:
        print("Failed:", ", ".join(failed_keys), flush=True)
        return 1
    return 0


def cmd_expand(args: argparse.Namespace) -> int:
    cats = _parse_cats(args.categories)
    n = expand_categories(cats, variants_per_task=args.variants_per_task)
    items = build_queue(categories=cats, include_expanded=True)
    write_manifest(items)
    print(f"Queue now {len(items)} items (base + expanded)", flush=True)
    print(f"Expanded files this run: {n}", flush=True)
    return 0


def cmd_reset_failed(args: argparse.Namespace) -> int:
    n = CheckpointStore().reset_failed()
    print(f"Reset {n} failed -> pending")
    return 0


def cmd_reset_built(args: argparse.Namespace) -> int:
    """Re-queue built (incomplete / deferred) tasks so autopilot finishes them."""
    keys = [k.strip() for k in (args.keys or "").split(",") if k.strip()] or None
    reset = CheckpointStore().reset_built(keys)
    print(f"Reset {len(reset)} built/running -> pending:")
    for k in reset:
        print(f"  - {k}")
    return 0


def _add_common(sp: argparse.ArgumentParser) -> None:
    sp.add_argument(
        "--categories",
        default=",".join(BIG_RUN_CATEGORIES),
        help="Comma-separated (default: ai_ml+games polish + 11 untouched)",
    )
    sp.add_argument("--base-only", action="store_true", help="Ignore expanded variants")
    sp.add_argument(
        "--force-all",
        action="store_true",
        help="Include already-strong demos (levellens/meritlens/etc)",
    )
    sp.add_argument("--model", default="kimi3")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="datagen_pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)

    st = sub.add_parser("status", help="Queue + checkpoint summary")
    _add_common(st)
    st.add_argument(
        "--recover",
        action="store_true",
        help="Convert stuck 'running' tasks back to pending (crash recovery)",
    )

    nxt = sub.add_parser("next", help="Write thin Chakra paste for next pending task")
    _add_common(nxt)

    md = sub.add_parser("mark-done", help="Checkpoint DONE after interactive run")
    _add_common(md)
    md.add_argument("--key", required=True)
    md.add_argument("--note", default="")
    md.add_argument("--no-next", action="store_true")
    md.add_argument("--force", action="store_true", help="Skip validate gate")
    md.add_argument("--skip-smoke", action="store_true")
    md.add_argument("--skip-seed", action="store_true")

    mf = sub.add_parser("mark-failed", help="Checkpoint failure")
    _add_common(mf)
    mf.add_argument("--key", required=True)
    mf.add_argument("--error", default="")

    mb = sub.add_parser(
        "mark-built",
        help="Checkpoint built (agent done; validate later / unblock sticky queue)",
    )
    _add_common(mb)
    mb.add_argument("--key", required=True)
    mb.add_argument("--note", default="")

    val = sub.add_parser("validate", help="Deterministic demo validate (structure/smoke/seed)")
    _add_common(val)
    val.add_argument("--key", default="")
    val.add_argument("--workdir", default="")
    val.add_argument("--language", default="")
    val.add_argument("--ui", default="")
    val.add_argument("--skip-smoke", action="store_true")
    val.add_argument("--skip-seed", action="store_true")
    val.add_argument("--smoke-timeout", type=int, default=120)

    rh = sub.add_parser("run-headless", help="Loop main.py one task at a time")
    _add_common(rh)
    rh.add_argument("--dry-run", action="store_true")
    rh.add_argument("--continue-on-error", action="store_true", default=True)
    rh.add_argument("--stop-on-error", action="store_true")
    rh.add_argument("--max-attempts", type=int, default=3)
    rh.add_argument("--skip-verification", action="store_true")
    rh.add_argument(
        "--skip-validate",
        action="store_true",
        help="Skip post-build validate gate (not recommended)",
    )
    rh.add_argument("--skip-smoke", action="store_true")
    rh.add_argument("--skip-seed", action="store_true")

    ap = sub.add_parser(
        "run-autopilot",
        help="ONE command: run all pending tasks via main.py (no manual paste)",
    )
    _add_common(ap)
    ap.add_argument("--dry-run", action="store_true")
    # LLM Phase-7 verify is optional (slow). Deterministic validate is the quality gate.
    ap.add_argument(
        "--skip-verification",
        action="store_true",
        default=True,
        help="Skip LLM verification subagent (default). Validate gate still runs.",
    )
    ap.add_argument(
        "--verify",
        action="store_true",
        help="Enable LLM verification subagent (Phase 7) in addition to validate",
    )
    ap.add_argument(
        "--skip-validate",
        action="store_true",
        help="Skip deterministic validate gate entirely",
    )
    ap.add_argument(
        "--defer-validate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Build-first: after agent OK, mark built and continue (default). "
        "Validate/repair runs in an end-of-queue pass. Use --no-defer-validate for old inline repair.",
    )
    ap.add_argument(
        "--repair-built",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="During end validate-pass, run one agent repair if validate fails (default on).",
    )
    ap.add_argument("--skip-smoke", action="store_true")
    ap.add_argument("--skip-seed", action="store_true")
    ap.add_argument("--smoke-timeout", type=int, default=120)
    ap.add_argument(
        "--max-retries",
        type=int,
        default=8,
        help="Per-task attempt budget inside one sticky cycle (timeouts/gRPC/503). Default 8.",
    )
    ap.add_argument(
        "--sticky-retries",
        type=int,
        default=20,
        help="Stay on same incomplete task this many failed cycles before moving on (default 20).",
    )
    ap.add_argument(
        "--failed-passes",
        type=int,
        default=1,
        help="After the main queue, re-try tasks that failed this run N times (default 1).",
    )
    ap.add_argument("--stop-on-error", action="store_true")
    ap.add_argument(
        "--expand-first",
        type=int,
        default=0,
        help="If >0, generate N variants per base task before running (~5k path)",
    )

    ex = sub.add_parser("expand", help="Create variant PRDs (~5k path)")
    _add_common(ex)
    ex.add_argument("--variants-per-task", type=int, default=45)

    sub.add_parser("reset-failed", help="failed -> pending")
    rb = sub.add_parser(
        "reset-built",
        help="built/running -> pending (finish incomplete tasks; do not skip)",
    )
    rb.add_argument(
        "--keys",
        default="",
        help="Comma-separated task keys (default: all built)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass
    # allow `python -m datagen_pipeline status`
    p = build_parser()
    args = p.parse_args(argv)
    if getattr(args, "stop_on_error", False):
        args.continue_on_error = False

    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "next":
        return cmd_next(args)
    if args.cmd == "mark-done":
        return cmd_mark_done(args)
    if args.cmd == "mark-failed":
        return cmd_mark_failed(args)
    if args.cmd == "mark-built":
        return cmd_mark_built(args)
    if args.cmd == "validate":
        return cmd_validate(args)
    if args.cmd == "run-headless":
        return cmd_run_headless(args)
    if args.cmd == "run-autopilot":
        from datagen_pipeline.autopilot import run_autopilot

        if getattr(args, "verify", False):
            args.skip_verification = False
        return run_autopilot(args)
    if args.cmd == "expand":
        return cmd_expand(args)
    if args.cmd == "reset-failed":
        return cmd_reset_failed(args)
    if args.cmd == "reset-built":
        return cmd_reset_built(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
