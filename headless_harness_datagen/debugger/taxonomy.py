"""Failure taxonomy for pipeline runs — causal primary over terminal outcomes."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from debugger.contracts.validate import ContractViolation
from debugger.load import LoadedRun
from debugger.metrics import RunMetrics
from debugger.phases import PhaseReport
from debugger.progress import ProgressAnalysis
from debugger.retries import DENIAL_LOOP_THRESHOLD, DenialSummary


@dataclass
class FailureItem:
    category: str
    subcategory: str
    message: str
    evidence_seqs: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FailureClassification:
    primary: FailureItem | None
    secondary: list[FailureItem]
    confidence: str  # high | medium | low
    recommendations: list[str]
    termination_outcome: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary": self.primary.to_dict() if self.primary else None,
            "secondary": [s.to_dict() for s in self.secondary],
            "confidence": self.confidence,
            "recommendations": self.recommendations,
            "termination_outcome": self.termination_outcome,
        }


# Causal priority (lower = more causal / preferred as primary)
_PRIORITY = {
    ("Provider", "Quota"): 10,
    ("Provider", "Timeout"): 10,
    ("Provider", "Authentication"): 10,
    ("Controller", "Exploration stall"): 20,
    ("Controller", "Forward progress stall"): 25,
    ("Controller", "Denial loop"): 30,
    ("Controller", "Wrong intervention"): 35,
    ("Controller", "Bad routing"): 36,
    ("Lifecycle", "Phase never reached"): 40,
    ("Lifecycle", "Invalid transition"): 45,
    ("Lifecycle", "Missing repair"): 46,
    ("Lifecycle", "Missing repair / exhausted"): 47,
    ("Verification", "False PASS"): 50,
    ("Implementation", "Failed"): 55,
    ("Implementation", "Runtime"): 56,
    ("Limits", "max_turns"): 90,
    ("Limits", "max_decisions"): 90,
    ("Limits", "Health terminate"): 91,
    ("Lifecycle", "Unknown"): 99,
}


def _priority(item: FailureItem) -> int:
    return _PRIORITY.get((item.category, item.subcategory), 80)


def _norm_subagent(raw: Any) -> str:
    return str(raw or "").strip().lower().replace("_", "-")


def classify_failures(
    run: LoadedRun,
    *,
    violations: list[ContractViolation] | None = None,
    metrics: RunMetrics | None = None,
    progress: ProgressAnalysis | None = None,
    phases: PhaseReport | None = None,
    denials: DenialSummary | None = None,
) -> FailureClassification:
    """Map run evidence to primary/secondary failure categories (causal first)."""
    violations = violations or []
    causal: list[FailureItem] = []
    outcomes: list[FailureItem] = []
    recommendations: list[str] = []

    term = None
    completed = None
    for rec in reversed(run.normalized):
        if rec.get("type") == "run_completed":
            term = rec.get("termination_reason")
            completed = rec.get("completed")
            break
    if term is None:
        term = run.summary.get("termination_reason")
        completed = run.summary.get("completed")

    life = run.summary.get("lifecycle_snapshot") or {}
    spawned = set()
    for rec in run.normalized:
        if rec.get("type") == "agent_spawn":
            args = rec.get("arguments") or {}
            spawned.add(_norm_subagent(args.get("subagent_type")))

    # --- Outcomes (demoted) ---
    if term in {"max_turns", "max_decisions"}:
        outcomes.append(
            FailureItem(
                category="Limits",
                subcategory=str(term),
                message=f"Run stopped at {term} (termination outcome)",
            )
        )

    # Live causal termination reasons (primary)
    term_s = str(term or "")
    if term_s == "no_forward_progress":
        causal.append(
            FailureItem(
                category="Controller",
                subcategory="Forward progress stall",
                message="Controller terminated: no_forward_progress",
            )
        )
        recommendations.append(
            "Investigate repeated soft-continues; look for denial loops or missing phase nudges"
        )
    elif term_s == "stuck_in_explore":
        causal.append(
            FailureItem(
                category="Controller",
                subcategory="Exploration stall",
                message="Controller terminated: stuck_in_explore",
            )
        )
        recommendations.append(
            "Spawn Plan then general-purpose; Explore alone will not advance the pipeline"
        )
    elif term_s == "denial_loop":
        causal.append(
            FailureItem(
                category="Controller",
                subcategory="Denial loop",
                message="Controller terminated: denial_loop",
            )
        )
        recommendations.append(
            "Stop retrying denied tools; adjust commands to stay in-repo or change approach"
        )
    elif term_s.startswith("phase_budget_exceeded:"):
        phase = term_s.split(":", 1)[-1]
        causal.append(
            FailureItem(
                category="Lifecycle",
                subcategory="Phase never reached"
                if phase in {"explore", "bootstrap"}
                else "Invalid transition",
                message=f"Phase budget exceeded: {phase}",
            )
        )
        recommendations.append(f"Tighten {phase} phase work or raise phase budget")

    if term == "max_repair_iterations" or life.get("repair_iterations_exhausted"):
        causal.append(
            FailureItem(
                category="Lifecycle",
                subcategory="Missing repair / exhausted",
                message="Repair iteration limit reached without PASS",
            )
        )
        recommendations.append("Inspect repeated FAIL causes; tighten repair plans")

    # --- Provider ---
    for rec in run.normalized:
        msg = str(rec.get("message") or rec.get("error") or "").lower()
        if rec.get("type") not in {"error", "run_failed", "turn_stall_cancelled"}:
            continue
        seqs = [rec.get("seq")] if rec.get("seq") else []
        if any(x in msg for x in ("quota", "rate limit", "429")):
            causal.append(
                FailureItem("Provider", "Quota", msg[:200], evidence_seqs=seqs)
            )
        elif any(x in msg for x in ("timeout", "deadline")):
            causal.append(
                FailureItem("Provider", "Timeout", msg[:200], evidence_seqs=seqs)
            )
        elif any(x in msg for x in ("auth", "unauthorized", "api key")):
            causal.append(
                FailureItem(
                    "Provider", "Authentication", msg[:200], evidence_seqs=seqs
                )
            )
        elif "stall" in msg or rec.get("type") == "turn_stall_cancelled":
            causal.append(
                FailureItem(
                    "Controller",
                    "Wrong intervention",
                    msg[:200] or "intervention stall loop",
                    evidence_seqs=seqs,
                )
            )
            recommendations.append("Review tool approval denials and stall thresholds")

    health = run.summary.get("health_snapshot") or {}
    if health.get("should_terminate") or (term and "health" in str(term).lower()):
        outcomes.append(
            FailureItem(
                category="Limits",
                subcategory="Health terminate",
                message=str(term or health.get("reason") or "session health terminate"),
            )
        )

    # --- Progress stall / exploration stall ---
    only_explore = bool(spawned) and spawned <= {"explore"} and "plan" not in spawned
    no_pipeline_agents = bool(spawned) and not (
        spawned & {"plan", "general-purpose", "generalpurpose", "verification", "verify"}
    )
    if progress and progress.forward_progress_stall:
        ev = []
        for s in progress.stalls:
            if s.start_seq is not None:
                ev.append(s.start_seq)
        if only_explore or no_pipeline_agents:
            causal.append(
                FailureItem(
                    category="Controller",
                    subcategory="Exploration stall",
                    message=(
                        f"Stuck exploring without Plan/implement "
                        f"({progress.max_consecutive_no_progress_cycles} resume cycles "
                        f"without forward progress)"
                    ),
                    evidence_seqs=ev[:5],
                )
            )
            recommendations.append(
                "Spawn Plan then general-purpose; Explore alone will not advance the pipeline"
            )
        else:
            causal.append(
                FailureItem(
                    category="Controller",
                    subcategory="Forward progress stall",
                    message=(
                        f"No meaningful progress for "
                        f"{progress.max_consecutive_no_progress_cycles} consecutive "
                        f"controller resume cycles (threshold="
                        f"{progress.stall_cycles_threshold})"
                    ),
                    evidence_seqs=ev[:5],
                )
            )
            recommendations.append(
                "Investigate repeated soft-continues; look for denial loops or missing phase nudges"
            )

    # --- Denial loops ---
    if denials and denials.top_group_count >= DENIAL_LOOP_THRESHOLD:
        top = denials.groups[0]
        causal.append(
            FailureItem(
                category="Controller",
                subcategory="Denial loop",
                message=top.message,
                evidence_seqs=[s for s in (top.first_seq, top.last_seq) if s is not None],
            )
        )
        recommendations.append(
            "Stop retrying denied tools; adjust commands to stay in-repo or change approach"
        )

    # --- Phase never reached vs failed ---
    if phases and completed is False:
        impl = phases.status_of("implementation")
        ver = phases.status_of("verification")
        repair = phases.status_of("repair")
        never = [
            p.phase
            for p in phases.phases
            if p.status == "never_reached"
            and p.phase in {"implementation", "verification", "repair"}
        ]
        stuck_before_pipeline = (
            only_explore
            or no_pipeline_agents
            or (progress is not None and progress.forward_progress_stall)
            or (denials is not None and denials.top_group_count >= DENIAL_LOOP_THRESHOLD)
        )
        if never and impl == "never_reached" and stuck_before_pipeline:
            causal.append(
                FailureItem(
                    category="Lifecycle",
                    subcategory="Phase never reached",
                    message=(
                        "Pipeline phases never entered: " + ", ".join(never)
                    ),
                )
            )
            recommendations.append(
                "Ensure Plan → general-purpose → verification sequencing begins after explore"
            )
        if impl == "failed" or (
            impl == "entered" and not life.get("implementation_complete_seen")
        ):
            if impl != "never_reached":
                causal.append(
                    FailureItem(
                        category="Implementation",
                        subcategory="Failed",
                        message="Implementation entered but did not reach COMPLETE",
                    )
                )
                recommendations.append(
                    "Inspect general-purpose agent output for ENV/IMPLEMENTATION markers"
                )
        if ver == "failed":
            causal.append(
                FailureItem(
                    category="Verification",
                    subcategory="False PASS"
                    if life.get("last_pass_rejection")
                    else "Failed",
                    message=next(
                        (p.evidence for p in phases.phases if p.phase == "verification"),
                        "Verification failed",
                    ),
                )
            )
        if repair == "failed":
            causal.append(
                FailureItem(
                    category="Lifecycle",
                    subcategory="Missing repair / exhausted",
                    message="Repair path entered but failed or exhausted",
                )
            )

    # Legacy: only flag missing IMPLEMENTATION when phase was entered
    if (
        not life.get("implementation_complete_seen")
        and completed is False
        and phases
        and phases.status_of("implementation") not in {"never_reached", "succeeded"}
    ):
        # Already covered by Failed above; skip duplicate Runtime message
        pass
    elif (
        not phases
        and not life.get("implementation_complete_seen")
        and completed is False
    ):
        causal.append(
            FailureItem(
                category="Implementation",
                subcategory="Runtime",
                message="Never saw IMPLEMENTATION_STATUS: COMPLETE",
            )
        )

    # Contract violations
    for v in violations:
        if v.rule_id == "verify.pass_requires_runtime_check":
            causal.append(
                FailureItem(
                    "Verification",
                    "False PASS",
                    v.message,
                    evidence_seqs=[v.evidence_seq] if v.evidence_seq else [],
                )
            )
            recommendations.append(
                "Ensure verification subagent emits RUNTIME_CHECK: PASS after real build/run"
            )
        elif v.rule_id == "verify.authoritative_source":
            causal.append(
                FailureItem(
                    "Verification",
                    "False PASS",
                    v.message,
                    evidence_seqs=[v.evidence_seq] if v.evidence_seq else [],
                )
            )
        elif v.rule_id == "repair.after_fail":
            causal.append(
                FailureItem("Lifecycle", "Missing repair", v.message)
            )
            recommendations.append("Confirm resume nudges fire repair_planning after FAIL")
        elif v.rule_id == "impl.before_verify":
            causal.append(
                FailureItem("Lifecycle", "Invalid transition", v.message)
            )
        elif v.rule_id.startswith("tools."):
            causal.append(
                FailureItem(
                    "Controller",
                    "Bad routing",
                    v.message,
                    evidence_seqs=[v.evidence_seq] if v.evidence_seq else [],
                )
            )

    # Success short-circuit
    if completed is True or str(run.verdict.get("verdict") or "").upper() == "PASS":
        if not causal and not outcomes:
            return FailureClassification(
                primary=None,
                secondary=[],
                confidence="high",
                recommendations=["Run completed successfully"],
                termination_outcome=str(term) if term else "completion",
            )

    def _dedupe(items: list[FailureItem]) -> list[FailureItem]:
        uniq: list[FailureItem] = []
        seen: set[tuple[str, str]] = set()
        for c in items:
            key = (c.category, c.subcategory)
            if key in seen:
                continue
            seen.add(key)
            uniq.append(c)
        return uniq

    causal = _dedupe(causal)
    outcomes = _dedupe(outcomes)
    causal.sort(key=_priority)

    if causal:
        primary = causal[0]
        secondary = causal[1:3] + outcomes[:2]
    elif outcomes:
        primary = outcomes[0]
        secondary = outcomes[1:3]
        recommendations.append(
            "Raise max_turns/max_decisions or fix stalls causing empty turns"
        )
    else:
        primary = FailureItem(
            category="Lifecycle",
            subcategory="Unknown",
            message=f"Run did not succeed (termination={term!r})",
        )
        secondary = []

    secondary = _dedupe(secondary)[:4]
    # Don't duplicate primary in secondary
    secondary = [
        s
        for s in secondary
        if (s.category, s.subcategory) != (primary.category, primary.subcategory)
    ]

    confidence = "high"
    if primary.category in {"Controller", "Lifecycle"} and primary.subcategory in {
        "Forward progress stall",
        "Exploration stall",
        "Phase never reached",
        "Denial loop",
    }:
        confidence = "high"
    elif primary.category == "Limits":
        confidence = "medium"

    rec_out: list[str] = []
    rseen: set[str] = set()
    for r in recommendations:
        if r not in rseen:
            rseen.add(r)
            rec_out.append(r)

    return FailureClassification(
        primary=primary,
        secondary=secondary,
        confidence=confidence,
        recommendations=rec_out,
        termination_outcome=str(term) if term else None,
    )
