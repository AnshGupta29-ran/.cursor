#!/usr/bin/env python3
"""Production entry point - single Chakra conversation (Phase 7).

Chakra owns plan -> implement -> verify -> repair -> re-verify.
Python only supervises: keep alive, approve tools, trace, detect completion.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

from adapter.chakra import ChakraHarness
from controller import OpenAICompatibleClient, new_run_id
from controller.conversation_config import ConversationConfig
from controller.conversation_runner import ConversationRunner
from controller.repo_bootstrap import ensure_project_git_repo
from controller.supervisor_policy import CompletionMode, SupervisorPolicy
from engine import ExecutionEngine
from scripts.real_backend import (
    connection_config,
    load_project_env,
    turn_timeout,
    working_directory,
)
from verification import Verdict, parse_verdict
from verification.prompts import (
    build_unified_pipeline_objective,
    write_harness_policy_file,
)
from verification.report import save_pipeline_artifacts, stage_working_run_id

ROOT = Path(__file__).resolve().parent
LOGS = ROOT / "logs"


def _run_pipeline(
    *,
    harness: ChakraHarness,
    llm,
    bootstrap: str,
    repo_dir: Path,
    run_log_root: Path,
    run_id: str,
    max_turns: int | None,
    max_decisions: int | None,
    max_repair_iterations: int,
    enable_trace: bool,
    completion_mode: CompletionMode,
    model: str | None = None,
) -> object:
    """Run one ConversationRunner / one conversation until completion or limit."""
    engine = ExecutionEngine(harness)
    policy = SupervisorPolicy(
        llm,
        bootstrap_message=bootstrap,
        completion_mode=completion_mode,
    )
    config = ConversationConfig.from_env(
        working_directory=str(repo_dir),
        max_turns=max_turns,
        max_decisions=max_decisions,
        max_repair_iterations=max_repair_iterations,
        turn_timeout_seconds=turn_timeout(),
        run_id=stage_working_run_id("pipeline"),
        log_root=run_log_root,
        enable_trace=enable_trace,
        model=(model or os.environ.get("OPENAI_MODEL") or None),
    )
    runner = ConversationRunner(engine, policy=policy, config=config)
    result = runner.run(bootstrap)
    save_pipeline_artifacts(
        run_log_root,
        run_id=run_id,
        objective=bootstrap,
        repository_path=str(repo_dir),
        controller_result=result.as_controller_result(),
        termination_reason=result.termination_reason,
        health_snapshot=result.health_snapshot,
        lifecycle_snapshot=result.lifecycle_snapshot,
    )
    return result


def main() -> int:
    # Windows consoles often use cp1252 - avoid crash on arrows/dashes in prints.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description=(
            "Autonomous harness - one Chakra conversation owns "
            "plan/implement/verify/repair (Phase 7)"
        )
    )
    parser.add_argument("objective", help="High-level project objective")
    parser.add_argument(
        "--workdir",
        default="autonomous_run",
        help="Subfolder under experiments/ for the working directory",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Run folder name under logs/ (default: auto-generated timestamp id)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=25,
        help="Safety cap on backend turns for the single conversation",
    )
    parser.add_argument(
        "--max-decisions",
        type=int,
        default=25,
        help="Safety cap on resume cycles for the single conversation",
    )
    parser.add_argument(
        "--no-trace",
        action="store_true",
        help="Disable JSONL conversation tracing",
    )
    parser.add_argument(
        "--max-repair-iterations",
        type=int,
        default=3,
        help="Max VERDICT: FAIL rounds before supervisor stops (Chakra owns the loop)",
    )
    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Generation only; complete on IMPLEMENTATION_STATUS: COMPLETE",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model id for Chakra gRPC ChatRequest (default: OPENAI_MODEL env)",
    )
    parser.add_argument(
        "--forge-prompt",
        action="store_true",
        help=(
            "Run prompt-forge mid-layer first: classify seed -> expand category "
            "template via LLM into a unique PLATFORM ADD-ON, then compose onto "
            "the normal harness bootstrap"
        ),
    )
    parser.add_argument(
        "--forge-category",
        default=None,
        help="Force prompt-forge category id (default: auto-classify)",
    )
    parser.add_argument(
        "--forge-llm-classify",
        action="store_true",
        help="Use LLM (not only heuristics) when auto-classifying category",
    )
    parser.add_argument(
        "--forge-temperature",
        type=float,
        default=1.0,
        help="Sampling temperature for unique platform prompt expansion (kimi3 requires 1)",
    )
    parser.add_argument(
        "--platform-prompt-file",
        default=None,
        help=(
            "Use an existing forged/expanded platform_prompt.md (skip live forge). "
            "Preferred for checkpointed datagen_pipeline runs."
        ),
    )
    args = parser.parse_args()

    load_project_env()
    run_id = args.run_id or new_run_id()
    run_log_root = LOGS / run_id
    repo_dir = Path(working_directory(args.workdir))
    enable_trace = not args.no_trace
    include_verification = not args.skip_verification
    completion_mode = (
        CompletionMode.IMPLEMENTATION_COMPLETE
        if args.skip_verification
        else CompletionMode.VERDICT_PASS
    )

    bootstrap = ensure_project_git_repo(repo_dir)
    if bootstrap.error:
        print(f"Error: git bootstrap failed for {repo_dir}: {bootstrap.error}")
        return 1
    if bootstrap.initialized:
        print(f"Initialized git repository at {repo_dir}")
    # Full SANDBOX dump in ChatRequest times out the proxy (0 tokens). Stage on disk.
    policy_path = write_harness_policy_file(repo_dir)
    print(f"Harness policy: {policy_path}")

    harness = ChakraHarness(default_timeout_seconds=turn_timeout())
    harness.connect(connection_config())
    llm = OpenAICompatibleClient.from_env()

    if args.platform_prompt_file:
        prd_path = Path(args.platform_prompt_file)
        if not prd_path.is_file():
            print(f"Error: --platform-prompt-file not found: {prd_path}")
            return 1
        platform_body = prd_path.read_text(encoding="utf-8")
        # Copy PRD inside the repo. Chakra Read/Bash on artifacts/ is sandboxed
        # (empty is_error) so the agent otherwise loops on a file it cannot open.
        local_prd = repo_dir / "platform_prompt.md"
        try:
            if prd_path.resolve() != local_prd.resolve():
                shutil.copy2(prd_path, local_prd)
        except OSError:
            local_prd.write_text(platform_body, encoding="utf-8")
        # Thin bootstrap: do NOT inline the full PRD (was 10k+ tokens every turn).
        # Agent must Read the in-repo copy once, then implement.
        objective = build_unified_pipeline_objective(
            repo_path=str(repo_dir),
            objective=(
                f"{args.objective}\n\n"
                f"PRD is {local_prd} — Read it ONCE, then Write code. "
                f"Do not Read artifacts/datagen_task_bank.\n"
            ),
            max_repair_iterations=args.max_repair_iterations,
            include_verification=include_verification,
        )
        print(f"=== Existing platform prompt ===\n{prd_path}")
        print(f"=== Copied into repo ===\n{local_prd}")
    elif args.forge_prompt:
        from prompt_forge.composer import compose_harness_objective, save_forge_artifacts

        print("=== Prompt forge (mid-layer) ===")
        forge = compose_harness_objective(
            repo_path=str(repo_dir),
            seed=args.objective,
            llm=llm,
            max_repair_iterations=args.max_repair_iterations,
            include_verification=include_verification,
            category=args.forge_category,
            use_llm_classifier=args.forge_llm_classify,
            temperature=args.forge_temperature,
        )
        forge_dir = run_log_root / "prompt_forge"
        paths = save_forge_artifacts(forge, forge_dir)
        objective = forge.composed_objective
        print(f"Category: {forge.category.value}")
        print(f"Forge artifacts: {forge_dir}")
        print(f"Platform prompt: {paths['platform_prompt']}")
    else:
        objective = build_unified_pipeline_objective(
            repo_path=str(repo_dir),
            objective=args.objective,
            max_repair_iterations=args.max_repair_iterations,
            include_verification=include_verification,
        )

    print(f"Run: {run_id}")
    print(f"Objective: {args.objective}")
    print(f"Repository: {repo_dir}")
    resolved_model = args.model or os.environ.get("OPENAI_MODEL") or "(chakra default)"
    print(f"Model: {resolved_model}")
    print(f"Logs: {run_log_root}")
    print(
        "Architecture: one Chakra conversation "
        "(plan->implement->verify->repair; Phase 7)"
    )
    print("\n=== Pipeline ===\n")

    try:
        result = _run_pipeline(
            harness=harness,
            llm=llm,
            bootstrap=objective,
            repo_dir=repo_dir,
            run_log_root=run_log_root,
            run_id=run_id,
            max_turns=args.max_turns,
            max_decisions=args.max_decisions,
            max_repair_iterations=args.max_repair_iterations,
            enable_trace=enable_trace,
            completion_mode=completion_mode,
            model=args.model,
        )
    finally:
        harness.disconnect()

    plan_file = repo_dir / "plan.md"
    if plan_file.is_file():
        print(f"Plan: {plan_file}")

    print(f"Completed: {result.completed}")
    print(f"Termination: {result.termination_reason}")
    if result.lifecycle_snapshot:
        print(
            "Lifecycle: "
            f"fails={result.lifecycle_snapshot.get('verdict_fail_count')} "
            f"pass={result.lifecycle_snapshot.get('verdict_pass_seen')} "
            f"repairs={result.lifecycle_snapshot.get('repair_complete_count')}"
        )
    summary_preview = result.summary or ""
    if len(summary_preview) > 300:
        print(f"Summary: {summary_preview[:300]}...")
    else:
        print(f"Summary: {summary_preview}")
    print(f"Backend turns: {result.turn_count}")
    print(f"Conversation id: {result.conversation_id}")
    if result.trace_path:
        print(f"Trace: {result.trace_path}")
        print(f"Raw events: {Path(result.trace_path).with_name('raw_events.jsonl')}")
    print(f"Artifacts: {run_log_root / 'pipeline'}")

    if result.termination_reason == "max_repair_iterations":
        print("\nStopped: max repair iterations reached (still one conversation).")
        return 1

    if not result.completed:
        print(f"\nPipeline did not complete ({result.termination_reason}).")
        return 1

    if args.skip_verification:
        print("\nGeneration complete (--skip-verification).")
        return 0

    life = result.lifecycle_snapshot or {}
    last = life.get("last_verdict")
    authoritative = bool(life.get("authoritative_pass"))
    verdict: Verdict | None = None
    if last:
        try:
            verdict = Verdict(str(last))
        except ValueError:
            verdict = None
    if verdict is None:
        verdict = parse_verdict(result.summary or "")

    print(f"Verdict: {verdict.value if verdict else 'NONE'}")
    if authoritative and verdict == Verdict.PASS:
        print("\nPipeline complete - verified by verification subagent.")
        return 0
    if verdict == Verdict.FAIL or verdict == Verdict.PARTIAL:
        print(f"\nVerification ended with {verdict.value}.")
        return 1
    print("\nNo authoritative VERDICT: PASS from the verification subagent.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
