"""Extract controller decision timeline from traces."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from debugger.load import LoadedRun


@dataclass
class DecisionEvent:
    seq: int | None
    ts: str | None
    decision: str
    kind: str | None
    reason: str
    source: str  # controller_decision | resume_nudge | tool_approval | inferred

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_NUDGE_REASONS = {
    "reverify_after_rejected_pass": "Rejected PASS — re-verify with runtime checks",
    "repair_planning": "Verification failed — begin repair planning",
    "repair_implementation": "Repair plan ready — apply fixes via general-purpose",
    "verification_rerun": "Repair complete — re-run verification",
    "implement": "Plan present — need env/implement markers",
    "verification": "Implementation complete — spawn verification",
    "neutral": "No lifecycle gap detected — soft continue",
}


def extract_decisions(run: LoadedRun) -> list[DecisionEvent]:
    """Chronological decisions from explicit logs or inferred resume_nudge events."""
    out: list[DecisionEvent] = []
    saw_controller_decision = False

    for rec in run.normalized:
        rtype = rec.get("type")
        if rtype == "controller_decision":
            saw_controller_decision = True
            out.append(
                DecisionEvent(
                    seq=rec.get("seq"),
                    ts=rec.get("ts"),
                    decision=str(rec.get("decision") or "unknown"),
                    kind=rec.get("kind"),
                    reason=str(rec.get("reason") or ""),
                    source="controller_decision",
                )
            )
        elif rtype == "resume_nudge":
            kind = str(rec.get("kind") or "")
            out.append(
                DecisionEvent(
                    seq=rec.get("seq"),
                    ts=rec.get("ts"),
                    decision="resume",
                    kind=kind,
                    reason=str(rec.get("reason") or _NUDGE_REASONS.get(kind, kind)),
                    source="resume_nudge",
                )
            )
        elif rtype == "tool_approval":
            out.append(
                DecisionEvent(
                    seq=rec.get("seq"),
                    ts=rec.get("ts"),
                    decision="tool_approval",
                    kind=str(rec.get("tool_name") or ""),
                    reason=str(rec.get("reasoning") or rec.get("response") or ""),
                    source="tool_approval",
                )
            )

    if not saw_controller_decision and out:
        # Older traces: mark that decision log is partial
        out.insert(
            0,
            DecisionEvent(
                seq=None,
                ts=None,
                decision="note",
                kind=None,
                reason="Partial decision log — controller_decision events absent (pre-instrumentation trace)",
                source="inferred",
            ),
        )
    return out
