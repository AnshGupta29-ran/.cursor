"""Text + HTML dashboard for prompt statistics."""

from __future__ import annotations

import json
import statistics
from collections import Counter
from html import escape
from pathlib import Path
from typing import Any

from prompt_stats.ledger import DASHBOARD_PATH, LATEST_PATH, ensure_stats_dir, load_records, utc_now


def summarize(records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    records = records if records is not None else load_records()
    by_source = Counter(r.get("source") or "?" for r in records)
    by_band = Counter(r.get("complexity_band") or "?" for r in records)
    by_category = Counter(
        r.get("category") for r in records if r.get("category")
    )
    scores = [float(r["complexity_score"]) for r in records if r.get("complexity_score") is not None]
    tokens = [int(r["est_tokens"]) for r in records if r.get("est_tokens") is not None]
    runtimes = [
        float(r["runtime_seconds"])
        for r in records
        if isinstance(r.get("runtime_seconds"), (int, float))
    ]
    turns = [
        int(r["turn_count"])
        for r in records
        if isinstance(r.get("turn_count"), int)
    ]

    def _avg(xs: list[float] | list[int]) -> float | None:
        return round(statistics.mean(xs), 2) if xs else None

    return {
        "generated_at": utc_now(),
        "total_records": len(records),
        "by_source": dict(by_source),
        "by_complexity_band": dict(by_band),
        "by_category": dict(by_category),
        "avg_complexity_score": _avg(scores),
        "avg_est_tokens": _avg(tokens),
        "avg_runtime_seconds": _avg(runtimes),
        "avg_turn_count": _avg(turns),
        "max_complexity_score": max(scores) if scores else None,
        "records_preview": sorted(
            records,
            key=lambda r: r.get("event_time") or r.get("recorded_at") or "",
            reverse=True,
        )[:50],
    }


def render_text_table(records: list[dict[str, Any]] | None = None) -> str:
    records = records if records is not None else load_records()
    rows = sorted(
        records,
        key=lambda r: r.get("event_time") or r.get("recorded_at") or "",
        reverse=True,
    )
    lines = [
        f"{'WHEN':<22} {'SRC':<18} {'BAND':<10} {'SCORE':>5} {'TOK~':>6} {'TIME':>8}  TITLE",
        "-" * 110,
    ]
    for r in rows:
        when = (r.get("event_time") or r.get("recorded_at") or "")[:19]
        src = str(r.get("source") or "")[:18]
        band = str(r.get("complexity_band") or "")[:10]
        score = r.get("complexity_score")
        score_s = f"{score:.0f}" if isinstance(score, (int, float)) else "-"
        tok = r.get("est_tokens")
        tok_s = str(tok) if tok is not None else "-"
        rt = r.get("runtime_seconds")
        rt_s = f"{rt:.0f}s" if isinstance(rt, (int, float)) else "-"
        title = str(r.get("title") or "")[:48].replace("\n", " ")
        lines.append(
            f"{when:<22} {src:<18} {band:<10} {score_s:>5} {tok_s:>6} {rt_s:>8}  {title}"
        )
    return "\n".join(lines)


def write_dashboard(records: list[dict[str, Any]] | None = None) -> Path:
    ensure_stats_dir()
    records = records if records is not None else load_records()
    summary = summarize(records)
    LATEST_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    rows_html = []
    for r in summary["records_preview"]:
        when = escape(str(r.get("event_time") or r.get("recorded_at") or "")[:19])
        src = escape(str(r.get("source") or ""))
        cat = escape(str(r.get("category") or "—"))
        band = escape(str(r.get("complexity_band") or "—"))
        score = r.get("complexity_score")
        score_s = f"{score:.1f}" if isinstance(score, (int, float)) else "—"
        toks = r.get("est_tokens")
        rt = r.get("runtime_seconds")
        turns = r.get("turn_count")
        verdict = escape(str(r.get("verdict") or "—"))
        title = escape(str(r.get("title") or "")[:100])
        rows_html.append(
            "<tr>"
            f"<td>{when}</td><td>{src}</td><td>{cat}</td><td>{band}</td>"
            f"<td>{score_s}</td><td>{toks if toks is not None else '—'}</td>"
            f"<td>{f'{rt:.0f}s' if isinstance(rt,(int,float)) else '—'}</td>"
            f"<td>{turns if turns is not None else '—'}</td><td>{verdict}</td>"
            f"<td>{title}</td>"
            "</tr>"
        )

    def chips(d: dict[str, Any]) -> str:
        if not d:
            return "<span class='muted'>none</span>"
        return " ".join(
            f"<span class='chip'>{escape(str(k))}: <b>{v}</b></span>"
            for k, v in sorted(d.items(), key=lambda kv: (-kv[1], str(kv[0])))
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Prompt statistics — headless_harness_datagen</title>
<style>
  :root {{ --bg:#0f1419; --card:#1a2332; --ink:#e7ecf3; --muted:#8b9bb4; --accent:#5b9fd4; }}
  body {{ margin:0; font-family:Segoe UI,system-ui,sans-serif; background:var(--bg); color:var(--ink); }}
  main {{ max-width:1200px; margin:0 auto; padding:24px; }}
  h1 {{ margin:0 0 6px; font-size:1.5rem; }}
  .sub {{ color:var(--muted); margin-bottom:20px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:12px; margin-bottom:20px; }}
  .card {{ background:var(--card); border:1px solid #2a3a50; border-radius:10px; padding:14px; }}
  .card .k {{ color:var(--muted); font-size:.8rem; }}
  .card .v {{ font-size:1.4rem; font-weight:600; margin-top:4px; }}
  .chip {{ display:inline-block; background:#243246; border-radius:999px; padding:4px 10px; margin:3px; font-size:.85rem; }}
  table {{ width:100%; border-collapse:collapse; font-size:.86rem; }}
  th,td {{ text-align:left; padding:8px 10px; border-bottom:1px solid #2a3a50; vertical-align:top; }}
  th {{ color:var(--muted); font-weight:600; }}
  .muted {{ color:var(--muted); }}
</style>
</head>
<body>
<main>
  <h1>Prompt statistics</h1>
  <p class="sub">Every Chakra-related prompt recorded in this repo · generated {escape(summary['generated_at'])}</p>
  <div class="grid">
    <div class="card"><div class="k">Total records</div><div class="v">{summary['total_records']}</div></div>
    <div class="card"><div class="k">Avg complexity</div><div class="v">{summary['avg_complexity_score'] if summary['avg_complexity_score'] is not None else '—'}</div></div>
    <div class="card"><div class="k">Avg est. tokens</div><div class="v">{summary['avg_est_tokens'] if summary['avg_est_tokens'] is not None else '—'}</div></div>
    <div class="card"><div class="k">Avg runtime</div><div class="v">{(str(summary['avg_runtime_seconds'])+'s') if summary['avg_runtime_seconds'] is not None else '—'}</div></div>
    <div class="card"><div class="k">Avg turns</div><div class="v">{summary['avg_turn_count'] if summary['avg_turn_count'] is not None else '—'}</div></div>
    <div class="card"><div class="k">Max complexity</div><div class="v">{summary['max_complexity_score'] if summary['max_complexity_score'] is not None else '—'}</div></div>
  </div>
  <div class="card" style="margin-bottom:16px"><div class="k">By source</div><div>{chips(summary['by_source'])}</div></div>
  <div class="card" style="margin-bottom:16px"><div class="k">By complexity band</div><div>{chips(summary['by_complexity_band'])}</div></div>
  <div class="card" style="margin-bottom:16px"><div class="k">By category</div><div>{chips(summary['by_category'])}</div></div>
  <div class="card">
    <div class="k" style="margin-bottom:10px">Recent prompts (up to 50)</div>
    <table>
      <thead><tr>
        <th>When</th><th>Source</th><th>Category</th><th>Band</th><th>Score</th>
        <th>Tok~</th><th>Time</th><th>Turns</th><th>Verdict</th><th>Title</th>
      </tr></thead>
      <tbody>
        {''.join(rows_html) if rows_html else '<tr><td colspan="10" class="muted">No records yet — run python -m prompt_stats refresh</td></tr>'}
      </tbody>
    </table>
  </div>
</main>
</body>
</html>
"""
    DASHBOARD_PATH.write_text(html, encoding="utf-8")
    return DASHBOARD_PATH
