"""Validate a loaded run against component contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from debugger.contracts.definitions import ALLOWED_SUBAGENT_TYPES, KNOWN_NUDGE_KINDS
from debugger.load import LoadedRun
from verification.parser import evaluation_rejects_pass


@dataclass
class ContractViolation:
    component: str
    rule_id: str
    severity: str  # error | warning
    message: str
    evidence_seq: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _norm_subagent(raw: Any) -> str:
    return str(raw or "").strip().lower().replace("_", "-")


def _lifecycle_from_run(run: LoadedRun) -> dict[str, Any]:
    life = run.summary.get("lifecycle_snapshot") or {}
    if life:
        return life
    for rec in reversed(run.normalized):
        orch = rec.get("orchestration") or {}
        nested = orch.get("lifecycle") or {}
        if nested:
            return nested
    return {}


def validate_contracts(run: LoadedRun) -> list[ContractViolation]:
    """Return contract violations found in the run artifacts."""
    violations: list[ContractViolation] = []
    normalized = run.normalized
    life = _lifecycle_from_run(run)

    # plan.before_implement
    impl_complete = bool(life.get("implementation_complete_seen"))
    plan_ok = bool(life.get("plan_done") or life.get("plan_agent_seen"))
    if impl_complete and not plan_ok:
        # Soft: also check Plan agent_spawn in trace
        saw_plan = any(
            r.get("type") == "agent_spawn"
            and _norm_subagent((r.get("arguments") or {}).get("subagent_type"))
            in {"plan"}
            for r in normalized
        )
        if not saw_plan:
            violations.append(
                ContractViolation(
                    component="plan",
                    rule_id="plan.before_implement",
                    severity="warning",
                    message="Implementation completed without Plan spawn or plan_done signal",
                )
            )

    # impl.before_verify — verification_result before implementation complete
    first_verify_seq = None
    for r in normalized:
        if r.get("type") == "verification_result":
            first_verify_seq = r.get("seq")
            break
    if first_verify_seq is not None and not impl_complete:
        # Only flag if lifecycle never saw implementation
        if not life.get("implementation_complete_seen"):
            violations.append(
                ContractViolation(
                    component="implementation",
                    rule_id="impl.before_verify",
                    severity="warning",
                    message="Verification result appeared without IMPLEMENTATION_STATUS: COMPLETE in lifecycle",
                    evidence_seq=int(first_verify_seq) if first_verify_seq else None,
                )
            )

    # verify.pass_requires_runtime_check — scan agent_completed / verification outputs
    for r in normalized:
        if r.get("type") != "verification_result":
            continue
        if str(r.get("verdict") or "").upper() != "PASS":
            continue
        # Look up paired agent output if present later in tool_pairs via invocation
        inv = r.get("invocation_id")
        output = ""
        for t in run.replay.tool_pairs:
            resp = t.get("response") or {}
            if inv and resp.get("invocation_id") == inv:
                output = str(resp.get("output") or "")
                break
        if not output:
            # Try agent_completed records
            for a in normalized:
                if a.get("type") == "agent_completed" and a.get("invocation_id") == inv:
                    output = str(a.get("output") or "")
                    break
        reject = evaluation_rejects_pass(output) if output else None
        if reject or (output and "RUNTIME_CHECK: PASS" not in output.upper().replace(" ", " ")):
            # evaluation_rejects_pass is authoritative when we have text
            if output and evaluation_rejects_pass(output):
                violations.append(
                    ContractViolation(
                        component="verification",
                        rule_id="verify.pass_requires_runtime_check",
                        severity="error",
                        message=f"VERDICT: PASS rejected by contract: {evaluation_rejects_pass(output)}",
                        evidence_seq=r.get("seq"),
                    )
                )
        # Also check lifecycle last_pass_rejection
    if life.get("last_pass_rejection"):
        violations.append(
            ContractViolation(
                component="verification",
                rule_id="verify.pass_requires_runtime_check",
                severity="error",
                message=f"Harness rejected PASS: {life.get('last_pass_rejection')}",
            )
        )

    # verify.authoritative_source — assistant_message alone claiming VERDICT without agent
    for r in normalized:
        if r.get("type") != "assistant_message":
            continue
        text = str(r.get("text") or "")
        if "VERDICT: PASS" in text.upper() or "VERDICT: FAIL" in text.upper():
            # Only warn if no verification_result nearby
            if not any(x.get("type") == "verification_result" for x in normalized):
                violations.append(
                    ContractViolation(
                        component="verification",
                        rule_id="verify.authoritative_source",
                        severity="warning",
                        message="Main assistant text contains VERDICT without verification_result events",
                        evidence_seq=r.get("seq"),
                    )
                )
                break

    # repair.after_fail
    fail_seen = any(
        r.get("type") == "verification_result"
        and str(r.get("verdict") or "").upper() in {"FAIL", "PARTIAL"}
        for r in normalized
    )
    if fail_seen:
        repair_nudge = any(
            r.get("type") in {"resume_nudge", "controller_decision"}
            and (
                r.get("kind") in {"repair_planning", "repair_implementation"}
                or (r.get("decision") == "resume" and r.get("kind") in {"repair_planning", "repair_implementation"})
            )
            for r in normalized
        )
        repair_gp = bool(life.get("repair_gp_seen_since_last_fail") or life.get("repair_complete_count"))
        completed = bool(run.summary.get("completed") or (run.verdict.get("verdict") or "").upper() == "PASS")
        if not repair_nudge and not repair_gp and not completed:
            # Check termination after fail without repair
            term = None
            for r in reversed(normalized):
                if r.get("type") == "run_completed":
                    term = r.get("termination_reason")
                    break
            if term and term != "completion":
                violations.append(
                    ContractViolation(
                        component="repair",
                        rule_id="repair.after_fail",
                        severity="warning",
                        message="Verification FAIL/PARTIAL seen but no repair nudge/GP before termination",
                    )
                )

    # nudge.known_kinds
    for r in normalized:
        if r.get("type") == "resume_nudge":
            kind = r.get("kind")
            if kind and kind not in KNOWN_NUDGE_KINDS:
                violations.append(
                    ContractViolation(
                        component="resume_nudges",
                        rule_id="nudge.known_kinds",
                        severity="error",
                        message=f"Unknown resume_nudge kind: {kind!r}",
                        evidence_seq=r.get("seq"),
                    )
                )
        if r.get("type") == "controller_decision" and r.get("decision") == "resume":
            kind = r.get("kind")
            if kind and kind not in KNOWN_NUDGE_KINDS:
                violations.append(
                    ContractViolation(
                        component="resume_nudges",
                        rule_id="nudge.known_kinds",
                        severity="error",
                        message=f"Unknown controller_decision resume kind: {kind!r}",
                        evidence_seq=r.get("seq"),
                    )
                )

    # health.termination_reason
    run_completed = [r for r in normalized if r.get("type") == "run_completed"]
    if run_completed:
        last = run_completed[-1]
        if not last.get("termination_reason") and last.get("completed") is False:
            violations.append(
                ContractViolation(
                    component="session_health",
                    rule_id="health.termination_reason",
                    severity="warning",
                    message="run_completed without termination_reason",
                    evidence_seq=last.get("seq"),
                )
            )
    elif normalized:
        # Has events but never completed — mid-run or crash
        violations.append(
            ContractViolation(
                component="session_health",
                rule_id="health.termination_reason",
                severity="warning",
                message="No run_completed event in trace",
            )
        )

    # tools.allowed_subagent
    for r in normalized:
        if r.get("type") != "agent_spawn":
            continue
        args = r.get("arguments") or {}
        sub = _norm_subagent(args.get("subagent_type"))
        if not sub:
            violations.append(
                ContractViolation(
                    component="tool_approval",
                    rule_id="tools.allowed_subagent",
                    severity="error",
                    message="Agent spawn missing subagent_type",
                    evidence_seq=r.get("seq"),
                )
            )
        elif sub not in ALLOWED_SUBAGENT_TYPES:
            violations.append(
                ContractViolation(
                    component="tool_approval",
                    rule_id="tools.allowed_subagent",
                    severity="error",
                    message=f"Unsupported subagent_type={args.get('subagent_type')!r}",
                    evidence_seq=r.get("seq"),
                )
            )

    return violations
