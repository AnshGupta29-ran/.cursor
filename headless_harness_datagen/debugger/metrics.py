"""Run metrics extraction and comparison."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from debugger.load import LoadedRun
from debugger.progress import ProgressAnalysis
from debugger.retries import DenialSummary


@dataclass
class RunMetrics:
    run_id: str | None
    runtime_seconds: float | None
    prompt_tokens: int
    completion_tokens: int
    agent_count: int
    agents_by_type: dict[str, int]
    tool_calls: int
    file_reads: int
    file_edits: int
    runtime_executions: int
    test_executions: int
    repair_iterations: int
    verification_failures: int
    duplicate_reads: int
    duplicate_edits: int
    final_status: str
    # Controller health
    max_consecutive_resumes_without_progress: int = 0
    forward_progress_stall: bool = False
    denied_tool_requests_by_reason: dict[str, int] = field(default_factory=dict)
    avg_seconds_between_progress_events: float | None = None
    denial_summary_count: int = 0
    top_denial_group_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def extract_metrics(
    run: LoadedRun,
    *,
    progress: ProgressAnalysis | None = None,
    denials: DenialSummary | None = None,
) -> RunMetrics:
    """Compute comparable metrics from a loaded run."""
    times: list[datetime] = []
    prompt = 0
    completion = 0
    agents_by_type: Counter[str] = Counter()
    tool_calls = 0
    reads: list[str] = []
    edits: list[str] = []
    runtime_exec = 0
    test_exec = 0
    verify_fail = 0

    for rec in run.normalized:
        t = _parse_ts(rec.get("ts"))
        if t:
            times.append(t)
        rtype = rec.get("type")
        if rtype == "token_usage":
            prompt += int(rec.get("prompt_tokens") or rec.get("input_tokens") or 0)
            completion += int(
                rec.get("completion_tokens") or rec.get("output_tokens") or 0
            )
        if rtype == "agent_spawn":
            args = rec.get("arguments") or {}
            sub = str(args.get("subagent_type") or "unknown")
            agents_by_type[sub] += 1
        if rtype in {"tool_request", "agent_spawn"}:
            tool_calls += 1
            name = str(rec.get("tool_name") or "")
            args = rec.get("arguments") or {}
            if name == "Read":
                path = str(args.get("file_path") or args.get("path") or "")
                if path:
                    reads.append(path)
            if name in {"Edit", "Write"}:
                path = str(args.get("file_path") or args.get("path") or "")
                if path:
                    edits.append(path)
            if name == "Bash" or args.get("command"):
                cmd = str(args.get("command") or "")
                if cmd:
                    runtime_exec += 1
                    low = cmd.lower()
                    if any(
                        x in low
                        for x in ("pytest", "npm test", "cargo test", "go test", "jest")
                    ):
                        test_exec += 1
        if rtype == "verification_result" and str(rec.get("verdict") or "").upper() in {
            "FAIL",
            "PARTIAL",
        }:
            verify_fail += 1

    life = run.summary.get("lifecycle_snapshot") or {}
    repair_iterations = int(life.get("verdict_fail_count") or verify_fail or 0)

    read_counts = Counter(reads)
    edit_counts = Counter(edits)
    dup_reads = sum(1 for _, c in read_counts.items() if c > 1)
    dup_edits = sum(1 for _, c in edit_counts.items() if c > 1)

    completed = run.summary.get("completed")
    if completed is None:
        for rec in reversed(run.normalized):
            if rec.get("type") == "run_completed":
                completed = rec.get("completed")
                break
    verdict = str(run.verdict.get("verdict") or "").upper()
    if completed is True or verdict == "PASS":
        final = "Passed"
    elif completed is False:
        final = "Failed"
    else:
        final = "Unknown"

    runtime = None
    if len(times) >= 2:
        runtime = (times[-1] - times[0]).total_seconds()

    # Prefer live pipeline_metrics when present
    live_metrics: dict[str, Any] = {}
    for rec in reversed(run.normalized):
        if rec.get("type") == "pipeline_metrics":
            live_metrics = dict(rec)
            break
        if rec.get("type") == "run_completed" and isinstance(
            rec.get("pipeline_metrics"), dict
        ):
            live_metrics = dict(rec["pipeline_metrics"])
            break

    max_no_progress = (
        int(live_metrics.get("consecutive_resumes_without_progress") or 0)
        if live_metrics
        else (progress.max_consecutive_no_progress_cycles if progress else 0)
    )
    if progress and progress.max_consecutive_no_progress_cycles > max_no_progress:
        max_no_progress = progress.max_consecutive_no_progress_cycles

    forward_stall = bool(
        live_metrics.get("progress", {}).get("is_stalled")
        if isinstance(live_metrics.get("progress"), dict)
        else False
    ) or (bool(progress.forward_progress_stall) if progress else False)

    denied_by_reason = dict(denials.by_reason) if denials else {}
    if isinstance(live_metrics.get("denials"), dict):
        live_by = live_metrics["denials"].get("by_reason")
        if isinstance(live_by, dict) and live_by:
            denied_by_reason = {str(k): int(v) for k, v in live_by.items()}

    return RunMetrics(
        run_id=run.run_id,
        runtime_seconds=runtime,
        prompt_tokens=prompt,
        completion_tokens=completion,
        agent_count=sum(agents_by_type.values()),
        agents_by_type=dict(agents_by_type),
        tool_calls=tool_calls,
        file_reads=len(reads),
        file_edits=len(edits),
        runtime_executions=runtime_exec,
        test_executions=test_exec,
        repair_iterations=repair_iterations,
        verification_failures=verify_fail,
        duplicate_reads=dup_reads,
        duplicate_edits=dup_edits,
        final_status=final,
        max_consecutive_resumes_without_progress=max_no_progress,
        forward_progress_stall=forward_stall,
        denied_tool_requests_by_reason=denied_by_reason,
        avg_seconds_between_progress_events=(
            progress.avg_seconds_between_progress_events if progress else None
        ),
        denial_summary_count=len(denials.groups) if denials else 0,
        top_denial_group_count=(
            int(
                (live_metrics.get("denials") or {}).get("top_group_count")
                or (denials.top_group_count if denials else 0)
            )
        ),
    )


def compare_metrics(a: RunMetrics, b: RunMetrics) -> list[dict[str, Any]]:
    """Return rows for a comparison table."""
    fields = [
        ("Runtime (s)", "runtime_seconds"),
        ("Prompt Tokens", "prompt_tokens"),
        ("Completion Tokens", "completion_tokens"),
        ("Agents", "agent_count"),
        ("Tool Calls", "tool_calls"),
        ("File Reads", "file_reads"),
        ("File Edits", "file_edits"),
        ("Runtime Executions", "runtime_executions"),
        ("Test Executions", "test_executions"),
        ("Repair Iterations", "repair_iterations"),
        ("Verification Failures", "verification_failures"),
        ("Duplicate Reads", "duplicate_reads"),
        ("Duplicate Edits", "duplicate_edits"),
        ("Max resumes w/o progress", "max_consecutive_resumes_without_progress"),
        ("Forward progress stall", "forward_progress_stall"),
        ("Avg sec between progress", "avg_seconds_between_progress_events"),
        ("Denial groups", "denial_summary_count"),
        ("Top denial group count", "top_denial_group_count"),
        ("Final Status", "final_status"),
    ]
    da, db = a.to_dict(), b.to_dict()
    rows = []
    for label, key in fields:
        rows.append({"metric": label, "run_a": da.get(key), "run_b": db.get(key)})
    return rows


def format_compare_table(rows: list[dict[str, Any]], *, label_a: str, label_b: str) -> str:
    lines = [
        f"| Metric | {label_a} | {label_b} |",
        "|---------|------:|------:|",
    ]
    for row in rows:
        lines.append(f"| {row['metric']} | {row['run_a']} | {row['run_b']} |")
    return "\n".join(lines)
