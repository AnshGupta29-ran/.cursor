"""Component contracts for harness pipeline validation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComponentContract:
    """Declarative contract for one pipeline component."""

    component: str
    purpose: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    success: tuple[str, ...]
    failure: tuple[str, ...]
    invariants: tuple[str, ...]
    rule_ids: tuple[str, ...]


CONTRACTS: tuple[ComponentContract, ...] = (
    ComponentContract(
        component="plan",
        purpose="Produce an implementation plan before coding.",
        inputs=("project objective", "repository root"),
        outputs=("plan.md and/or Plan subagent completion",),
        success=("plan_done or plan_agent_seen before implementation complete",),
        failure=("implementation without any plan signal",),
        invariants=(
            "Prefer Plan spawn or plan.md before IMPLEMENTATION_STATUS: COMPLETE",
        ),
        rule_ids=("plan.before_implement",),
    ),
    ComponentContract(
        component="implementation",
        purpose="Create env and implement the plan via general-purpose.",
        inputs=("plan.md", "repository"),
        outputs=("ENV_STATUS: READY", "IMPLEMENTATION_STATUS: COMPLETE"),
        success=("both env and implementation markers from general-purpose",),
        failure=("verification started without implementation complete",),
        invariants=(
            "ENV_STATUS: READY and IMPLEMENTATION_STATUS: COMPLETE before first accepted verify",
        ),
        rule_ids=("impl.before_verify",),
    ),
    ComponentContract(
        component="verification",
        purpose="Adversarial verify via verification subagent only.",
        inputs=("repository", "objective", "plan"),
        outputs=("VERDICT", "RUNTIME_CHECK"),
        success=("VERDICT: PASS with RUNTIME_CHECK: PASS from verification Agent",),
        failure=("PASS without RUNTIME_CHECK", "self-assigned verdict"),
        invariants=(
            "PASS cannot occur without RUNTIME_CHECK: PASS",
            "Authoritative VERDICT only from verification Agent tool evidence",
        ),
        rule_ids=(
            "verify.pass_requires_runtime_check",
            "verify.authoritative_source",
        ),
    ),
    ComponentContract(
        component="repair",
        purpose="Repair after FAIL/PARTIAL then re-verify.",
        inputs=("verifier report", "repair_plan.md"),
        outputs=("REPAIR_STATUS: COMPLETE", "re-verification"),
        success=("repair path then new verification cycle",),
        failure=("FAIL with no repair nudge/action before end",),
        invariants=(
            "After FAIL/PARTIAL, repair planning and/or GP repair should precede "
            "next verify when run continues",
        ),
        rule_ids=("repair.after_fail",),
    ),
    ComponentContract(
        component="resume_nudges",
        purpose="Python steers Chakra via phase-aware resume messages.",
        inputs=("lifecycle snapshot",),
        outputs=("resume_nudge kind + message",),
        success=("nudge kind matches lifecycle gap when non-neutral",),
        failure=("stuck soft-continue while repair needed",),
        invariants=("Logged non-neutral nudge kinds are from the known set",),
        rule_ids=("nudge.known_kinds",),
    ),
    ComponentContract(
        component="session_health",
        purpose="Terminate unhealthy or limit-exceeded sessions.",
        inputs=("timeouts", "turn/repair limits"),
        outputs=("termination_reason",),
        success=("clean completion or explicit limit/health reason",),
        failure=("run ends without run_completed record",),
        invariants=("termination_reason present on run_completed",),
        rule_ids=("health.termination_reason",),
    ),
    ComponentContract(
        component="tool_approval",
        purpose="Auto-approve or deny Agent/tool interventions.",
        inputs=("tool name", "arguments"),
        outputs=("yes/no approval",),
        success=("Agent spawns include allowed subagent_type",),
        failure=("Agent without subagent_type",),
        invariants=(
            "Agent subagent_type ∈ Plan|general-purpose|verification|Explore",
        ),
        rule_ids=("tools.allowed_subagent",),
    ),
)


KNOWN_NUDGE_KINDS = frozenset(
    {
        "neutral",
        "implement",
        "verification",
        "verification_rerun",
        "repair_planning",
        "repair_implementation",
        "reverify_after_rejected_pass",
    }
)

ALLOWED_SUBAGENT_TYPES = frozenset(
    {
        "plan",
        "general-purpose",
        "generalpurpose",
        "verification",
        "verify",
        "explore",
    }
)
