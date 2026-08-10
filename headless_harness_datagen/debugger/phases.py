"""Phase reachability diagnosis — never_reached vs entered/failed/succeeded."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from debugger.load import LoadedRun


PhaseStatus = str  # never_reached | entered | succeeded | failed


@dataclass
class PhaseDiagnosis:
    phase: str
    status: PhaseStatus
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PhaseReport:
    phases: list[PhaseDiagnosis] = field(default_factory=list)

    def status_of(self, phase: str) -> PhaseStatus:
        for p in self.phases:
            if p.phase == phase:
                return p.status
        return "never_reached"

    def to_dict(self) -> dict[str, Any]:
        return {"phases": [p.to_dict() for p in self.phases]}


def _norm_subagent(raw: Any) -> str:
    return str(raw or "").strip().lower().replace("_", "-")


def _lifecycle(run: LoadedRun) -> dict[str, Any]:
    life = run.summary.get("lifecycle_snapshot") or {}
    if life:
        return life
    for rec in reversed(run.normalized):
        orch = rec.get("orchestration") or {}
        nested = orch.get("lifecycle") or {}
        if nested:
            return nested
    return {}


def diagnose_phases(run: LoadedRun) -> PhaseReport:
    """Classify plan / implementation / verification / repair reachability."""
    life = _lifecycle(run)
    spawned: set[str] = set()
    verify_results: list[str] = []
    saw_repair_nudge = False
    saw_repair_complete = False

    for rec in run.normalized:
        rtype = rec.get("type")
        if rtype == "agent_spawn":
            args = rec.get("arguments") or {}
            spawned.add(_norm_subagent(args.get("subagent_type")))
        elif rtype == "verification_result":
            verify_results.append(str(rec.get("verdict") or "").upper())
        elif rtype in {"resume_nudge", "controller_decision"}:
            kind = str(rec.get("kind") or "")
            if kind in {"repair_planning", "repair_implementation", "verification_rerun"}:
                saw_repair_nudge = True
        out = str(rec.get("output") or "")
        if "REPAIR_STATUS: COMPLETE" in out.upper():
            saw_repair_complete = True

    # --- plan ---
    plan_spawn = "plan" in spawned
    if life.get("plan_done"):
        plan_status: PhaseStatus = "succeeded"
        plan_ev = "plan_done"
    elif plan_spawn or life.get("plan_agent_seen"):
        plan_status = "entered"
        plan_ev = "Plan agent spawned / plan_agent_seen"
    else:
        plan_status = "never_reached"
        plan_ev = "No Plan spawn or plan.md / plan_done signal"

    # --- implementation (Explore does not count; main Writes count as entered) ---
    gp_spawn = "general-purpose" in spawned or "generalpurpose" in spawned
    impl_complete = bool(life.get("implementation_complete_seen"))
    env_ready = bool(life.get("env_ready_seen"))
    main_writes = int(life.get("main_agent_write_count") or 0)
    if not main_writes:
        # Count Write tool_requests in trace if lifecycle missing the field
        main_writes = sum(
            1
            for r in run.normalized
            if r.get("type") == "tool_request"
            and str(r.get("tool_name") or "") in {"Write", "Edit", "MultiEdit"}
        )
    if impl_complete:
        impl_status: PhaseStatus = "succeeded"
        impl_ev = "IMPLEMENTATION_STATUS: COMPLETE seen"
    elif gp_spawn or env_ready:
        impl_status = "entered"
        impl_ev = "general-purpose spawned or ENV_STATUS seen without COMPLETE"
    elif main_writes > 0:
        impl_status = "entered"
        impl_ev = (
            f"main-agent writes without general-purpose / COMPLETE marker "
            f"({main_writes} Write/Edit)"
        )
    else:
        impl_status = "never_reached"
        impl_ev = "Implementation never entered (no general-purpose / markers)"

    # --- verification ---
    verify_spawn = "verification" in spawned or "verify" in spawned
    if life.get("authoritative_pass") or (
        any(v == "PASS" for v in verify_results) and not life.get("last_pass_rejection")
    ):
        ver_status: PhaseStatus = "succeeded"
        ver_ev = "Authoritative VERDICT: PASS"
    elif life.get("last_pass_rejection"):
        ver_status = "failed"
        ver_ev = f"PASS rejected: {life.get('last_pass_rejection')}"
    elif any(v in {"FAIL", "PARTIAL"} for v in verify_results):
        ver_status = "failed"
        ver_ev = f"VERDICT: {verify_results[-1]}"
    elif verify_spawn or verify_results:
        ver_status = "entered"
        ver_ev = "Verification agent spawned or result recorded"
    else:
        ver_status = "never_reached"
        ver_ev = "Verification never entered (no verification agent / VERDICT)"

    # --- repair ---
    if saw_repair_complete or life.get("repair_complete_count"):
        repair_status: PhaseStatus = "succeeded"
        repair_ev = "REPAIR_STATUS: COMPLETE or repair_complete_count"
    elif life.get("repair_iterations_exhausted"):
        repair_status = "failed"
        repair_ev = "Repair iterations exhausted"
    elif (
        saw_repair_nudge
        or life.get("repair_plan_done")
        or life.get("repair_gp_seen_since_last_fail")
    ):
        repair_status = "entered"
        repair_ev = "Repair path started (nudge / plan / GP)"
    else:
        repair_status = "never_reached"
        repair_ev = "Repair never entered"

    return PhaseReport(
        phases=[
            PhaseDiagnosis("plan", plan_status, plan_ev),
            PhaseDiagnosis("implementation", impl_status, impl_ev),
            PhaseDiagnosis("verification", ver_status, ver_ev),
            PhaseDiagnosis("repair", repair_status, repair_ev),
        ]
    )
