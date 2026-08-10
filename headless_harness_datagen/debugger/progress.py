"""Forward-progress detection across controller resume cycles.

Workflow progress (phase transitions / milestones) resets stall counters.
Tool activity (Reads, Edits, agent churn) is recorded separately and does not.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from debugger.load import LoadedRun

DEFAULT_STALL_CYCLES = 5

_WORKFLOW_MARKER_RES = (
    (re.compile(r"IMPLEMENTATION_STATUS\s*:\s*COMPLETE", re.I), "milestone_implementation"),
    (re.compile(r"ENV_STATUS\s*:\s*READY", re.I), "milestone_env"),
    (re.compile(r"REPAIR_STATUS\s*:\s*COMPLETE", re.I), "milestone_repair"),
)

_PIPELINE_AGENTS = frozenset(
    {"plan", "general-purpose", "generalpurpose", "verification", "verify"}
)


@dataclass
class ProgressEvent:
    seq: int | None
    ts: str | None
    kind: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StallWindow:
    start_seq: int | None
    end_seq: int | None
    cycles_without_progress: int
    last_progress_kind: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProgressAnalysis:
    progress_events: list[ProgressEvent] = field(default_factory=list)
    stalls: list[StallWindow] = field(default_factory=list)
    forward_progress_stall: bool = False
    max_consecutive_no_progress_cycles: int = 0
    avg_seconds_between_progress_events: float | None = None
    stall_cycles_threshold: int = DEFAULT_STALL_CYCLES

    def to_dict(self) -> dict[str, Any]:
        return {
            "progress_events": [e.to_dict() for e in self.progress_events],
            "stalls": [s.to_dict() for s in self.stalls],
            "forward_progress_stall": self.forward_progress_stall,
            "max_consecutive_no_progress_cycles": self.max_consecutive_no_progress_cycles,
            "avg_seconds_between_progress_events": self.avg_seconds_between_progress_events,
            "stall_cycles_threshold": self.stall_cycles_threshold,
        }


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


def _norm_subagent(raw: Any) -> str:
    return str(raw or "").strip().lower().replace("_", "-")


def _is_resume_cycle(rec: dict[str, Any]) -> bool:
    rtype = rec.get("type")
    if rtype == "controller_decision" and rec.get("decision") == "resume":
        return True
    if rtype == "resume_nudge":
        return True
    return False


def _scan_progress_in_record(
    rec: dict[str, Any],
    *,
    seen_pipeline_agents: set[str],
    seen_milestones: set[str],
    plan_seen: bool,
) -> tuple[list[ProgressEvent], bool]:
    """
    Return (workflow progress events, plan_seen_updated).

    Activity-only records contribute nothing to stall reset.
    """
    events: list[ProgressEvent] = []
    rtype = rec.get("type")
    seq = rec.get("seq")
    ts = rec.get("ts")

    if rtype == "agent_spawn":
        args = rec.get("arguments") or {}
        sub = _norm_subagent(args.get("subagent_type"))
        if sub in _PIPELINE_AGENTS and sub not in seen_pipeline_agents:
            seen_pipeline_agents.add(sub)
            # First Plan spawn ≈ phase transition / plan milestone
            if sub == "plan" and "plan" not in seen_milestones:
                seen_milestones.add("plan")
                events.append(
                    ProgressEvent(seq=seq, ts=ts, kind="milestone_plan", detail=sub)
                )
                plan_seen = True
            elif sub in {"general-purpose", "generalpurpose"}:
                events.append(
                    ProgressEvent(
                        seq=seq, ts=ts, kind="phase_transition", detail=f"spawn:{sub}"
                    )
                )
            elif sub in {"verification", "verify"}:
                events.append(
                    ProgressEvent(
                        seq=seq, ts=ts, kind="phase_transition", detail=f"spawn:{sub}"
                    )
                )
    elif rtype == "verification_result":
        verdict = str(rec.get("verdict") or "").upper()
        if verdict in {"PASS", "FAIL", "PARTIAL"} and "verify" not in seen_milestones:
            # Only authoritative-style results; rejected PASS still may appear
            if verdict == "PASS" or verdict in {"FAIL", "PARTIAL"}:
                seen_milestones.add("verify")
                events.append(
                    ProgressEvent(
                        seq=seq, ts=ts, kind="milestone_verify", detail=verdict
                    )
                )
    elif rtype == "controller_decision" and rec.get("decision") == "recover":
        # Recovery itself is not workflow progress
        pass

    text_blobs = [
        str(rec.get("output") or ""),
        str(rec.get("text") or ""),
        str(rec.get("message") or ""),
        str((rec.get("arguments") or {}).get("prompt") or ""),
    ]
    blob = "\n".join(text_blobs)
    for regex, kind in _WORKFLOW_MARKER_RES:
        key = kind
        if regex.search(blob) and key not in seen_milestones:
            seen_milestones.add(key)
            events.append(ProgressEvent(seq=seq, ts=ts, kind=kind, detail=key))

    # plan.md existence signals in lifecycle snapshots
    orch = rec.get("orchestration") or {}
    life = orch.get("lifecycle") or rec.get("lifecycle") or {}
    if isinstance(life, dict):
        if (life.get("plan_done") or life.get("plan_agent_seen")) and "plan" not in seen_milestones:
            seen_milestones.add("plan")
            events.append(
                ProgressEvent(seq=seq, ts=ts, kind="milestone_plan", detail="lifecycle")
            )
            plan_seen = True
        if life.get("implementation_complete_seen") and "milestone_implementation" not in seen_milestones:
            seen_milestones.add("milestone_implementation")
            events.append(
                ProgressEvent(
                    seq=seq, ts=ts, kind="milestone_implementation", detail="lifecycle"
                )
            )
        if life.get("authoritative_pass") and "verify" not in seen_milestones:
            seen_milestones.add("verify")
            events.append(
                ProgressEvent(seq=seq, ts=ts, kind="milestone_verify", detail="PASS")
            )

    # Summary-level plan.md mention alone is weak; require plan.md write tool
    if rtype == "tool_request":
        name = str(rec.get("tool_name") or "")
        args = rec.get("arguments") or {}
        path = str(args.get("file_path") or args.get("path") or "")
        if name in {"Write", "Edit"} and path.endswith("plan.md") and "plan" not in seen_milestones:
            seen_milestones.add("plan")
            events.append(
                ProgressEvent(seq=seq, ts=ts, kind="milestone_plan", detail=path)
            )
            plan_seen = True

    return events, plan_seen


def analyze_progress(
    run: LoadedRun,
    *,
    stall_cycles: int = DEFAULT_STALL_CYCLES,
) -> ProgressAnalysis:
    """
    Walk the trace and detect forward-progress stalls across resume cycles.

    A controller cycle is each resume decision. Only workflow milestones between
    cycles reset the consecutive no-progress counter.
    """
    threshold = max(1, int(stall_cycles))
    seen_pipeline_agents: set[str] = set()
    seen_milestones: set[str] = set()
    plan_seen = False
    all_progress: list[ProgressEvent] = []
    stalls: list[StallWindow] = []

    consecutive = 0
    max_consecutive = 0
    stall_start_seq: int | None = None
    last_progress_kind: str | None = None
    pending_progress: list[ProgressEvent] = []

    # Also scan summary lifecycle once at start
    life = (run.summary or {}).get("lifecycle_snapshot") or {}
    if life.get("plan_done") or life.get("plan_agent_seen"):
        seen_milestones.add("plan")
        plan_seen = True

    for rec in run.normalized:
        pevents, plan_seen = _scan_progress_in_record(
            rec,
            seen_pipeline_agents=seen_pipeline_agents,
            seen_milestones=seen_milestones,
            plan_seen=plan_seen,
        )
        if pevents:
            pending_progress.extend(pevents)
            all_progress.extend(pevents)
            last_progress_kind = pevents[-1].kind

        if not _is_resume_cycle(rec):
            continue

        cycle_seq = rec.get("seq")
        if pending_progress:
            if consecutive >= threshold:
                stalls.append(
                    StallWindow(
                        start_seq=stall_start_seq,
                        end_seq=cycle_seq,
                        cycles_without_progress=consecutive,
                        last_progress_kind=last_progress_kind,
                    )
                )
            consecutive = 0
            stall_start_seq = None
            pending_progress = []
        else:
            consecutive += 1
            if stall_start_seq is None:
                stall_start_seq = cycle_seq
            max_consecutive = max(max_consecutive, consecutive)

    if consecutive >= threshold:
        end_seq = None
        for rec in reversed(run.normalized):
            if _is_resume_cycle(rec) or rec.get("type") == "run_completed":
                end_seq = rec.get("seq")
                break
        stalls.append(
            StallWindow(
                start_seq=stall_start_seq,
                end_seq=end_seq,
                cycles_without_progress=consecutive,
                last_progress_kind=last_progress_kind,
            )
        )

    avg_gap: float | None = None
    times = [_parse_ts(e.ts) for e in all_progress]
    times = [t for t in times if t is not None]
    if len(times) >= 2:
        gaps = [
            (times[i] - times[i - 1]).total_seconds()
            for i in range(1, len(times))
            if times[i] >= times[i - 1]
        ]
        if gaps:
            avg_gap = sum(gaps) / len(gaps)

    return ProgressAnalysis(
        progress_events=all_progress,
        stalls=stalls,
        forward_progress_stall=bool(stalls) or max_consecutive >= threshold,
        max_consecutive_no_progress_cycles=max_consecutive,
        avg_seconds_between_progress_events=avg_gap,
        stall_cycles_threshold=threshold,
    )
