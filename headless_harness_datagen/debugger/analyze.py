"""Phase 2 run analyzer — structured offline analysis."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any

from debugger.contracts.validate import ContractViolation, validate_contracts
from debugger.decisions import DecisionEvent, extract_decisions
from debugger.load import LoadedRun
from debugger.metrics import RunMetrics, extract_metrics
from debugger.phases import PhaseReport, diagnose_phases
from debugger.progress import DEFAULT_STALL_CYCLES, ProgressAnalysis, analyze_progress
from debugger.retries import DenialSummary, summarize_denials
from debugger.taxonomy import FailureClassification, classify_failures


@dataclass
class TimelineEntry:
    seq: int | None
    ts: str | None
    type: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentEvent:
    seq: int | None
    invocation_id: str | None
    subagent_type: str | None
    event: str  # spawn | completed
    preview: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunAnalysis:
    run_id: str | None
    pipeline_dir: str
    timeline: list[TimelineEntry]
    agents: list[AgentEvent]
    tool_counts: dict[str, int]
    bash_commands: list[str]
    files_read: list[str]
    files_edited: list[str]
    token_events: list[dict[str, Any]]
    compact_events: list[dict[str, Any]]
    verification_history: list[dict[str, Any]]
    repair_history: list[dict[str, Any]]
    decisions: list[DecisionEvent]
    termination_reason: str | None
    completed: bool | None
    contract_violations: list[ContractViolation]
    failure: FailureClassification
    metrics: RunMetrics
    progress: ProgressAnalysis | None = None
    phases: PhaseReport | None = None
    denials: DenialSummary | None = None
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "pipeline_dir": self.pipeline_dir,
            "timeline": [t.to_dict() for t in self.timeline],
            "agents": [a.to_dict() for a in self.agents],
            "tool_counts": self.tool_counts,
            "bash_commands": self.bash_commands,
            "files_read": self.files_read,
            "files_edited": self.files_edited,
            "token_events": self.token_events,
            "compact_events": self.compact_events,
            "verification_history": self.verification_history,
            "repair_history": self.repair_history,
            "decisions": [d.to_dict() for d in self.decisions],
            "termination_reason": self.termination_reason,
            "completed": self.completed,
            "contract_violations": [v.to_dict() for v in self.contract_violations],
            "failure": self.failure.to_dict(),
            "metrics": self.metrics.to_dict(),
            "progress": self.progress.to_dict() if self.progress else None,
            "phases": self.phases.to_dict() if self.phases else None,
            "denials": self.denials.to_dict() if self.denials else None,
            "recommendations": self.recommendations,
        }


_SKIP_TIMELINE = frozenset({"assistant_text_delta"})


def _brief(rec: dict[str, Any]) -> str:
    rtype = str(rec.get("type") or "")
    if rtype == "agent_spawn":
        args = rec.get("arguments") or {}
        return f"spawn {args.get('subagent_type')}"
    if rtype == "agent_completed":
        return f"agent done inv={rec.get('invocation_id')}"
    if rtype == "resume_nudge":
        return f"nudge={rec.get('kind')}"
    if rtype == "controller_decision":
        return f"{rec.get('decision')}:{rec.get('kind') or ''} {rec.get('reason') or ''}".strip()
    if rtype == "verification_result":
        return f"VERDICT:{rec.get('verdict')}"
    if rtype == "run_completed":
        return f"done completed={rec.get('completed')} reason={rec.get('termination_reason')}"
    if rtype == "tool_request":
        return f"tool {rec.get('tool_name')}"
    if rtype in {"token_usage", "context_compacted"}:
        return rtype
    if rtype == "error":
        return str(rec.get("message") or "error")[:120]
    return rtype


def analyze_run(
    run: LoadedRun,
    *,
    stall_cycles: int = DEFAULT_STALL_CYCLES,
) -> RunAnalysis:
    """Build a full structured analysis for a loaded pipeline run."""
    timeline: list[TimelineEntry] = []
    agents: list[AgentEvent] = []
    tool_counts: Counter[str] = Counter()
    bash_commands: list[str] = []
    files_read: list[str] = []
    files_edited: list[str] = []
    token_events: list[dict[str, Any]] = []
    compact_events: list[dict[str, Any]] = []
    verification_history: list[dict[str, Any]] = []
    repair_history: list[dict[str, Any]] = []
    termination_reason: str | None = None
    completed: bool | None = None

    for rec in run.normalized:
        rtype = str(rec.get("type") or "")
        if rtype not in _SKIP_TIMELINE and rtype not in {
            "assistant_message",
            "stream_turn_started",
            "stream_turn_finished",
            "backend_turn_start",
            "backend_turn_completed",
            "backend_intervention_response",
            "intervention_required",
            "intervention_resolved",
            "engine_notification",
        }:
            timeline.append(
                TimelineEntry(
                    seq=rec.get("seq"),
                    ts=rec.get("ts"),
                    type=rtype,
                    summary=_brief(rec),
                )
            )

        if rtype == "agent_spawn":
            args = rec.get("arguments") or {}
            agents.append(
                AgentEvent(
                    seq=rec.get("seq"),
                    invocation_id=rec.get("invocation_id"),
                    subagent_type=args.get("subagent_type"),
                    event="spawn",
                    preview=str(args.get("description") or args.get("prompt") or "")[:160],
                )
            )
        elif rtype == "agent_completed":
            agents.append(
                AgentEvent(
                    seq=rec.get("seq"),
                    invocation_id=rec.get("invocation_id"),
                    subagent_type=None,
                    event="completed",
                    preview=str(rec.get("output") or "")[:160],
                )
            )

        if rtype in {"tool_request", "agent_spawn"}:
            name = str(rec.get("tool_name") or ("Agent" if rtype == "agent_spawn" else "unknown"))
            tool_counts[name] += 1
            args = rec.get("arguments") or {}
            if name == "Bash" or "command" in args:
                cmd = str(args.get("command") or "")
                if cmd:
                    bash_commands.append(cmd)
            if name == "Read":
                path = str(args.get("file_path") or args.get("path") or "")
                if path:
                    files_read.append(path)
            if name in {"Edit", "Write"}:
                path = str(args.get("file_path") or args.get("path") or "")
                if path:
                    files_edited.append(path)

        if rtype == "token_usage":
            token_events.append(
                {
                    "seq": rec.get("seq"),
                    "prompt_tokens": rec.get("prompt_tokens") or rec.get("input_tokens"),
                    "completion_tokens": rec.get("completion_tokens")
                    or rec.get("output_tokens"),
                }
            )
        if rtype == "context_compacted":
            compact_events.append(
                {"seq": rec.get("seq"), "kind": rec.get("kind"), "ts": rec.get("ts")}
            )

        if rtype == "verification_result":
            verification_history.append(
                {
                    "seq": rec.get("seq"),
                    "verdict": rec.get("verdict"),
                    "invocation_id": rec.get("invocation_id"),
                }
            )

        if rtype == "resume_nudge" and rec.get("kind") in {
            "repair_planning",
            "repair_implementation",
            "verification_rerun",
        }:
            repair_history.append(
                {
                    "seq": rec.get("seq"),
                    "kind": rec.get("kind"),
                    "preview": rec.get("message_preview"),
                }
            )
        if rtype == "controller_decision" and rec.get("kind") in {
            "repair_planning",
            "repair_implementation",
            "verification_rerun",
        }:
            repair_history.append(
                {
                    "seq": rec.get("seq"),
                    "kind": rec.get("kind"),
                    "reason": rec.get("reason"),
                }
            )

        if rtype == "run_completed":
            termination_reason = rec.get("termination_reason")
            completed = rec.get("completed")

    if completed is None and run.summary:
        completed = run.summary.get("completed")
        termination_reason = termination_reason or run.summary.get("termination_reason")

    life = run.summary.get("lifecycle_snapshot") or {}
    if life.get("last_pass_rejection"):
        verification_history.append(
            {
                "seq": None,
                "verdict": "REJECTED_PASS",
                "reason": life.get("last_pass_rejection"),
            }
        )

    progress = analyze_progress(run, stall_cycles=stall_cycles)
    phases = diagnose_phases(run)
    denials = summarize_denials(run)
    violations = validate_contracts(run)
    decisions = extract_decisions(run)
    metrics = extract_metrics(run, progress=progress, denials=denials)
    failure = classify_failures(
        run,
        violations=violations,
        metrics=metrics,
        progress=progress,
        phases=phases,
        denials=denials,
    )

    recommendations = list(failure.recommendations)
    for v in violations:
        if v.severity == "error":
            recommendations.append(f"Fix contract {v.rule_id}: {v.message}")

    return RunAnalysis(
        run_id=run.run_id,
        pipeline_dir=str(run.pipeline_dir),
        timeline=timeline,
        agents=agents,
        tool_counts=dict(tool_counts),
        bash_commands=bash_commands,
        files_read=files_read,
        files_edited=files_edited,
        token_events=token_events,
        compact_events=compact_events,
        verification_history=verification_history,
        repair_history=repair_history,
        decisions=decisions,
        termination_reason=str(termination_reason) if termination_reason else None,
        completed=completed if isinstance(completed, bool) else None,
        contract_violations=violations,
        failure=failure,
        metrics=metrics,
        progress=progress,
        phases=phases,
        denials=denials,
        recommendations=_dedupe(recommendations),
    )


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out
