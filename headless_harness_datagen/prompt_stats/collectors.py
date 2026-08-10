"""Backfill collectors — harvest past prompts from known locations."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from prompt_stats.hooks import record_forge_event, record_pipeline_event, record_raw_prompt
from prompt_stats.ledger import REPO_ROOT


def collect_chakra_sessions() -> int:
    from prompt_stats.chakra_sessions import collect_chakra_sessions as _collect

    return _collect()


def collect_pi_sessions() -> int:
    from prompt_stats.pi_sessions import collect_pi_sessions as _collect

    return _collect()


def collect_task_bank() -> int:
    """Upsert seeds from artifacts/datagen_task_bank/by_category/*/*.json."""
    root = REPO_ROOT / "artifacts" / "datagen_task_bank" / "by_category"
    if not root.is_dir():
        return 0
    n = 0
    for jp in sorted(root.glob("*/*.json")):
        try:
            data = json.loads(jp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        seed = (data.get("seed") or "").strip()
        if not seed:
            continue
        cat = data.get("category") or jp.parent.name
        record_raw_prompt(
            prompt=seed,
            source="task_bank",
            title=data.get("title"),
            category=cat,
            project=data.get("workdir"),
            extra={
                "task_id": data.get("id"),
                "workdir": data.get("workdir"),
                "dimensions_hint": data.get("dimensions_hint"),
                "batch": f"{cat}_all_10",
                "path_hint": str(jp.relative_to(REPO_ROOT)).replace("\\", "/"),
            },
        )
        n += 1
    return n


def refresh_all() -> dict[str, int]:
    """Scan repo + Chakra history and append missing ledger rows."""
    counts = {
        "forge_artifacts": collect_forge_artifacts(),
        "pipeline_logs": collect_pipeline_logs(),
        "project_prompts": collect_project_prompts_md(),
        "task_bank": collect_task_bank(),
        "chakra_sessions": collect_chakra_sessions(),
        "chakra_history": collect_chakra_history(),
        "pi_sessions": collect_pi_sessions(),
        "experiments_readmes": collect_experiment_readmes(),
    }
    # Re-link session time/tokens after forge/readme upserts may overwrite ests
    from prompt_stats.chakra_sessions import enrich_ledger_from_sessions

    counts["session_enrich"] = enrich_ledger_from_sessions()
    return counts


def collect_forge_artifacts() -> int:
    n = 0
    roots = [
        REPO_ROOT / "artifacts",
        REPO_ROOT / "logs",
    ]
    for root in roots:
        if not root.is_dir():
            continue
        for meta in root.rglob("forge_meta.json"):
            try:
                data = json.loads(meta.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            run_id = None
            # logs/<run-id>/prompt_forge/forge_meta.json
            parts = meta.parts
            if "logs" in parts:
                try:
                    i = parts.index("logs")
                    run_id = parts[i + 1]
                except (ValueError, IndexError):
                    run_id = None
            record_forge_event(
                seed=data.get("seed") or "",
                platform_prompt=data.get("platform_prompt") or "",
                category=data.get("category"),
                classification=data.get("classification"),
                template_used=data.get("template_used"),
                out_dir=meta.parent,
                run_id=run_id,
            )
            n += 1
    return n


def collect_pipeline_logs() -> int:
    n = 0
    logs = REPO_ROOT / "logs"
    if not logs.is_dir():
        return 0
    for summary_path in logs.rglob("summary.json"):
        # Prefer pipeline/summary.json; also accept flat legacy summary.json
        if summary_path.parent.name not in {"pipeline", "generation", "verification"}:
            if summary_path.parent.parent.name == "logs":
                pass  # legacy flat
            elif "pipeline" not in summary_path.parts:
                continue
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if "objective" not in summary and "run_id" not in summary:
            continue
        run_id = summary.get("run_id") or summary_path.parent.parent.name
        forge_meta = None
        forge_path = summary_path.parent.parent / "prompt_forge" / "forge_meta.json"
        if not forge_path.is_file():
            # flat: logs/<id>/ vs logs/<id>/pipeline/
            alt = summary_path.parent / "prompt_forge" / "forge_meta.json"
            forge_path = alt if alt.is_file() else forge_path
        if forge_path.is_file():
            try:
                forge_meta = json.loads(forge_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                forge_meta = None
        prompt_tok, completion_tok, runtime = _tokens_from_trace(
            summary_path.parent / "trace.jsonl"
        )
        record_pipeline_event(
            run_id=str(run_id),
            objective=summary.get("objective") or "",
            repository_path=summary.get("repository_path"),
            summary=summary,
            runtime_seconds=runtime,
            forge_meta=forge_meta,
            prompt_tokens=prompt_tok,
            completion_tokens=completion_tok,
        )
        n += 1
    return n


def collect_project_prompts_md() -> int:
    path = REPO_ROOT / "docs" / "archive" / "project_prompts.md"
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8")
    # Split numbered prompts like "1. Title\nCreate a ..."
    chunks = re.split(r"(?m)^(?=\d+\.\s)", text)
    n = 0
    for chunk in chunks:
        chunk = chunk.strip()
        if len(chunk) < 80:
            continue
        m = re.match(r"(\d+)\.\s*([^\n]+)\n([\s\S]*)", chunk)
        if not m:
            continue
        num, title, body = m.group(1), m.group(2).strip(), m.group(3).strip()
        # Keep only the prompt body before next structural divider if huge
        body = body.split("⸻")[0].split("Bonus Challenge")[0].strip()
        if len(body) < 40:
            body = title
        prompt = f"{title}\n\n{body}".strip()
        record_raw_prompt(
            prompt=prompt,
            source="project_prompts_md",
            title=f"{num}. {title}",
            extra={"archive_index": int(num)},
        )
        n += 1
    return n


def collect_chakra_history() -> int:
    """Import short prompts from history.jsonl; skip sessions already covered.

    Call collect_chakra_sessions() first from sync/refresh so time/tokens are current.
    """
    hist = Path.home() / ".chakra" / "history.jsonl"
    if not hist.is_file():
        return 0
    repo_marker = str(REPO_ROOT).replace("/", "\\").lower()
    known_sessions = {
        str(r.get("session_id") or "")
        for r in __import__("prompt_stats.ledger", fromlist=["load_records"]).load_records()
        if r.get("source") == "chakra_session"
    }
    n = 0
    with hist.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            project = str(row.get("project") or "")
            if repo_marker not in project.replace("/", "\\").lower():
                continue
            sid = str(row.get("sessionId") or "")
            if sid and sid in known_sessions:
                continue
            display = str(row.get("display") or "").strip()
            if not display or display.startswith("/"):
                continue
            if display.startswith("[Pasted text"):
                # Prefer session transcript for pasted PRDs
                if sid:
                    continue
            pasted = row.get("pastedContents") or {}
            if isinstance(pasted, dict) and pasted:
                chunks = []
                for _k, v in pasted.items():
                    if isinstance(v, dict) and v.get("content"):
                        chunks.append(str(v["content"]))
                    elif isinstance(v, str):
                        chunks.append(v)
                if chunks:
                    display = "\n\n".join(chunks)
            ts = row.get("timestamp")
            event_time = None
            if isinstance(ts, (int, float)):
                if ts > 1e14:
                    ts = ts / 1e6
                elif ts > 1e11:
                    ts = ts / 1e3
                try:
                    event_time = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                except (OSError, OverflowError, ValueError):
                    event_time = None
            record_raw_prompt(
                prompt=display,
                source="chakra_history",
                title=display[:80].replace("\n", " "),
                session_id=sid,
                project=project,
                extra={"event_time": event_time} if event_time else None,
            )
            n += 1
    return n


def collect_experiment_readmes() -> int:
    """Index generated experiment / chakra-cwd projects via README titles."""
    n = 0
    candidates = [
        REPO_ROOT / "experiments",
        REPO_ROOT / "harness" / "chakra",
    ]
    skip_names = {
        "node_modules",
        ".git",
        "src",
        "dist",
        "docs",
        "scripts",
        ".venv",
        "tests",
        ".pytest_cache",
        "bin",
        "vscode-extension",
    }
    for base in candidates:
        if not base.is_dir():
            continue
        for readme in base.rglob("README.md"):
            if any(part in skip_names for part in readme.parts):
                continue
            # Only shallow-ish project readmes
            rel = readme.relative_to(base)
            if len(rel.parts) > 3:
                continue
            try:
                text = readme.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            title = None
            for line in text.splitlines()[:15]:
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            if not title or len(text) < 120:
                continue
            record_raw_prompt(
                prompt=text[:3000],
                source="generated_project_readme",
                title=title,
                project=str(readme.parent),
                extra={"readme_path": str(readme)},
            )
            n += 1
    return n


def _tokens_from_trace(trace_path: Path) -> tuple[int | None, int | None, float | None]:
    """Return (prompt_tokens, completion_tokens, runtime_seconds) from a trace.jsonl."""
    if not trace_path.is_file():
        return None, None, None
    first = last = None
    prompt = 0
    completion = 0
    saw_tokens = False
    try:
        with trace_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = row.get("ts")
                if ts:
                    if first is None:
                        first = ts
                    last = ts
                rtype = row.get("type") or row.get("normalized_type")
                if rtype == "token_usage":
                    saw_tokens = True
                    prompt += int(
                        row.get("prompt_tokens")
                        or row.get("input_tokens")
                        or 0
                    )
                    completion += int(
                        row.get("completion_tokens")
                        or row.get("output_tokens")
                        or 0
                    )
                usage = row.get("usage")
                if isinstance(usage, dict):
                    saw_tokens = True
                    prompt += int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
                    completion += int(
                        usage.get("completion_tokens") or usage.get("output_tokens") or 0
                    )
        runtime = None
        if first and last:
            a = datetime.fromisoformat(str(first).replace("Z", "+00:00"))
            b = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
            runtime = round((b - a).total_seconds(), 2)
        return (prompt if saw_tokens else None, completion if saw_tokens else None, runtime)
    except (OSError, ValueError):
        return None, None, None


def _runtime_from_trace(trace_path: Path) -> float | None:
    _p, _c, runtime = _tokens_from_trace(trace_path)
    return runtime
