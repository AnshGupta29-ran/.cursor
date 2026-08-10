"""Markdown + JSON report writers for debugger analyses."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from debugger.analyze import RunAnalysis
from debugger.metrics import format_compare_table


def write_report(analysis: RunAnalysis, *, out_dir: Path | None = None) -> Path:
    """Write report.md + report.json under pipeline/debug/."""
    debug_dir = out_dir or (Path(analysis.pipeline_dir) / "debug")
    debug_dir.mkdir(parents=True, exist_ok=True)

    json_path = debug_dir / "report.json"
    md_path = debug_dir / "report.md"

    payload = analysis.to_dict()
    json_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(analysis), encoding="utf-8")
    return debug_dir


def render_markdown(analysis: RunAnalysis) -> str:
    m = analysis.metrics
    f = analysis.failure
    outcome = f.termination_outcome or analysis.termination_reason
    lines: list[str] = [
        f"# Debugger report — {analysis.run_id or 'unknown'}",
        "",
        "## Executive summary",
        "",
        f"- **Completed:** {analysis.completed}",
        f"- **Termination outcome:** {outcome or 'n/a'}",
        f"- **Final status:** {m.final_status}",
        f"- **Primary failure (causal):** {_fmt_primary(f)}",
        f"- **Contract violations:** {len(analysis.contract_violations)} "
        f"({sum(1 for v in analysis.contract_violations if v.severity == 'error')} errors)",
        "",
        "## Metrics",
        "",
        f"| Metric | Value |",
        f"|--------|------:|",
        f"| Runtime (s) | {m.runtime_seconds} |",
        f"| Prompt tokens | {m.prompt_tokens} |",
        f"| Completion tokens | {m.completion_tokens} |",
        f"| Agents | {m.agent_count} ({m.agents_by_type}) |",
        f"| Tool calls | {m.tool_calls} |",
        f"| File reads / edits | {m.file_reads} / {m.file_edits} |",
        f"| Runtime / test execs | {m.runtime_executions} / {m.test_executions} |",
        f"| Repair iterations | {m.repair_iterations} |",
        f"| Verification failures | {m.verification_failures} |",
        "",
        "## Controller health",
        "",
        f"| Metric | Value |",
        f"|--------|------:|",
        f"| Max resumes without progress | {m.max_consecutive_resumes_without_progress} |",
        f"| Forward progress stall | {m.forward_progress_stall} |",
        f"| Avg seconds between progress | {m.avg_seconds_between_progress_events} |",
        f"| Denial groups | {m.denial_summary_count} |",
        f"| Top denial group count | {m.top_denial_group_count} |",
        "",
    ]
    if m.denied_tool_requests_by_reason:
        lines.append("Denied tool requests by reason:")
        lines.append("")
        for reason, count in sorted(
            m.denied_tool_requests_by_reason.items(), key=lambda x: -x[1]
        ):
            lines.append(f"- ({count}) {reason}")
        lines.append("")

    lines.extend(["## Phase diagnosis", ""])
    if analysis.phases and analysis.phases.phases:
        for p in analysis.phases.phases:
            lines.append(f"- **{p.phase}:** `{p.status}` — {p.evidence}")
    else:
        lines.append("_Unavailable_")
    lines.append("")

    lines.extend(["## Progress / stalls", ""])
    if analysis.progress:
        pr = analysis.progress
        lines.append(
            f"- Stall threshold: {pr.stall_cycles_threshold} cycles; "
            f"max consecutive without progress: {pr.max_consecutive_no_progress_cycles}; "
            f"forward_progress_stall={pr.forward_progress_stall}"
        )
        if pr.stalls:
            for s in pr.stalls:
                lines.append(
                    f"- Stall seq {s.start_seq}→{s.end_seq}: "
                    f"{s.cycles_without_progress} cycles "
                    f"(last progress: {s.last_progress_kind})"
                )
        else:
            lines.append("- No stall windows at current threshold")
        lines.append(f"- Progress events: {len(pr.progress_events)}")
    else:
        lines.append("_Unavailable_")
    lines.append("")

    lines.extend(["## Denial summaries", ""])
    if analysis.denials and analysis.denials.groups:
        for g in analysis.denials.groups[:20]:
            lines.append(
                f"- {g.message} (seq {g.first_seq}→{g.last_seq})"
            )
        if len(analysis.denials.groups) > 20:
            lines.append(f"- … {len(analysis.denials.groups) - 20} more groups")
    else:
        lines.append("_None_")
    lines.append("")

    lines.extend(["## Failure classification", ""])
    if f.primary:
        lines.append(
            f"- **Primary** ({f.confidence}): `{f.primary.category}` / "
            f"`{f.primary.subcategory}` — {f.primary.message}"
        )
    else:
        lines.append("- **Primary:** none (success or no classification)")
    if outcome:
        lines.append(f"- **Termination outcome:** {outcome}")
    for s in f.secondary:
        lines.append(f"- Secondary: `{s.category}` / `{s.subcategory}` — {s.message}")
    lines.extend(["", "## Recommendations", ""])
    for r in analysis.recommendations or ["(none)"]:
        lines.append(f"- {r}")

    lines.extend(["", "## Contract violations", ""])
    if not analysis.contract_violations:
        lines.append("_None_")
    else:
        for v in analysis.contract_violations:
            lines.append(
                f"- **[{v.severity}]** `{v.component}` `{v.rule_id}` "
                f"(seq={v.evidence_seq}): {v.message}"
            )

    lines.extend(["", "## Agent lifecycle", ""])
    for a in analysis.agents[:80]:
        lines.append(
            f"- seq={a.seq} `{a.event}` type={a.subagent_type} "
            f"inv={a.invocation_id} {a.preview[:80]}"
        )
    if len(analysis.agents) > 80:
        lines.append(f"- … {len(analysis.agents) - 80} more")

    lines.extend(["", "## Verification history", ""])
    if not analysis.verification_history:
        lines.append("_None_")
    else:
        for vh in analysis.verification_history:
            lines.append(f"- {vh}")

    lines.extend(["", "## Repair history", ""])
    if not analysis.repair_history:
        lines.append("_None_")
    else:
        for rh in analysis.repair_history:
            lines.append(f"- {rh}")

    lines.extend(["", "## Controller decisions", ""])
    _append_decisions_section(lines, analysis)

    lines.extend(["", "## Timeline (abbreviated)", ""])
    for t in analysis.timeline[:120]:
        lines.append(f"- [{t.seq}] {t.type}: {t.summary}")
    if len(analysis.timeline) > 120:
        lines.append(f"- … {len(analysis.timeline) - 120} more events")

    lines.append("")
    return "\n".join(lines)


def _append_decisions_section(lines: list[str], analysis: RunAnalysis) -> None:
    """Summaries first; omit raw denial spam from decision list."""
    if analysis.denials and analysis.denials.groups:
        lines.append("_Denial groups (collapsed):_")
        for g in analysis.denials.groups[:15]:
            lines.append(f"- {g.message}")
        lines.append("")

    if not analysis.decisions:
        lines.append("_None logged_")
        return

    shown = 0
    skipped_denials = 0
    for d in analysis.decisions:
        if d.source == "tool_approval":
            reason_l = (d.reason or "").lower()
            if reason_l.startswith("deny") or reason_l.startswith("no"):
                skipped_denials += 1
                continue
        lines.append(
            f"- seq={d.seq} [{d.source}] `{d.decision}` kind={d.kind} — {d.reason}"
        )
        shown += 1
        if shown >= 80:
            break
    if skipped_denials:
        lines.append(
            f"- … {skipped_denials} individual denial approvals omitted "
            "(see Denial summaries)"
        )
    remaining = len(analysis.decisions) - shown - skipped_denials
    if remaining > 0 and shown >= 80:
        lines.append(f"- … {remaining} more decision events")


def _fmt_primary(f: Any) -> str:
    if not f.primary:
        return "none"
    return f"{f.primary.category}/{f.primary.subcategory}"


def write_compare(
    rows: list[dict[str, Any]],
    *,
    label_a: str,
    label_b: str,
    out_path: Path | None = None,
) -> str:
    table = format_compare_table(rows, label_a=label_a, label_b=label_b)
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "run_a": label_a,
            "run_b": label_b,
            "rows": rows,
        }
        out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        md = out_path.with_suffix(".md")
        md.write_text(f"# Compare {label_a} vs {label_b}\n\n{table}\n", encoding="utf-8")
    return table
