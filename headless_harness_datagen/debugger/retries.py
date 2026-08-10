"""Group repeated identical tool denials for readable reports."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any

from debugger.load import LoadedRun

DENIAL_LOOP_THRESHOLD = 5


@dataclass
class DenialGroup:
    tool_name: str
    reason: str
    sample_target: str
    count: int
    first_seq: int | None
    last_seq: int | None
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DenialSummary:
    groups: list[DenialGroup] = field(default_factory=list)
    by_reason: dict[str, int] = field(default_factory=dict)
    total_denials: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "groups": [g.to_dict() for g in self.groups],
            "by_reason": self.by_reason,
            "total_denials": self.total_denials,
        }

    @property
    def top_group_count(self) -> int:
        return max((g.count for g in self.groups), default=0)


def _is_denial(reason: str, response: str) -> bool:
    text = f"{response} {reason}".strip().lower()
    return text.startswith("deny") or text.startswith("no") or " deny " in f" {text}"


def _reason_bucket(reason: str) -> str:
    r = (reason or "").strip()
    if not r:
        return "unknown"
    return r if len(r) <= 120 else r[:117] + "..."


def summarize_denials(run: LoadedRun) -> DenialSummary:
    """Collapse identical denied tool approvals into grouped summaries."""
    requests_by_seq: list[tuple[int, str, str]] = []
    for rec in run.normalized:
        if rec.get("type") != "tool_request":
            continue
        seq = rec.get("seq")
        if seq is None:
            continue
        name = str(rec.get("tool_name") or "")
        args = rec.get("arguments") or {}
        target = str(
            args.get("command") or args.get("file_path") or args.get("path") or ""
        ).strip()
        requests_by_seq.append((int(seq), name, target))

    def nearest_target(approval_seq: int, tool_name: str) -> str:
        best = ""
        best_seq = -1
        for seq, name, target in requests_by_seq:
            if name != tool_name:
                continue
            if seq < approval_seq and seq > best_seq:
                best_seq = seq
                best = target
        return best

    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    by_reason: dict[str, int] = defaultdict(int)
    total = 0

    for rec in run.normalized:
        if rec.get("type") != "tool_approval":
            continue
        reason = str(rec.get("reasoning") or "")
        response = str(rec.get("response") or "")
        if not _is_denial(reason, response):
            continue
        total += 1
        tool = str(rec.get("tool_name") or "unknown")
        bucket = _reason_bucket(reason or response)
        by_reason[bucket] += 1
        seq = rec.get("seq")
        target = nearest_target(int(seq), tool) if seq is not None else ""
        key = (tool, target or "(unknown)", bucket)
        if key not in groups:
            groups[key] = {
                "tool_name": tool,
                "reason": bucket,
                "sample_target": target,
                "count": 0,
                "first_seq": seq,
                "last_seq": seq,
            }
        g = groups[key]
        g["count"] += 1
        g["last_seq"] = seq
        if g["first_seq"] is None:
            g["first_seq"] = seq

    out_groups: list[DenialGroup] = []
    for g in sorted(groups.values(), key=lambda x: -x["count"]):
        tool = g["tool_name"]
        count = g["count"]
        target = g["sample_target"]
        reason = g["reason"]
        sample = f" (`{target[:80]}`)" if target else ""
        if count == 1:
            msg = f"{tool} denied once: {reason}"
        elif "outside repository" in reason.lower():
            msg = (
                f"Repeated identical {tool} denied {count} times "
                f"(outside repository / destructive){sample}"
            )
        else:
            msg = f"Repeated identical {tool} command denied {count} times{sample}"
        out_groups.append(
            DenialGroup(
                tool_name=tool,
                reason=reason,
                sample_target=target,
                count=count,
                first_seq=g["first_seq"],
                last_seq=g["last_seq"],
                message=msg,
            )
        )

    return DenialSummary(
        groups=out_groups,
        by_reason=dict(by_reason),
        total_denials=total,
    )
