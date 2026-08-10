"""Parse ~/.pi/agent/sessions JSONL for duration, tokens, models, tasks."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from prompt_stats.metrics import (
    analyze_prompt_text,
    apply_effort_complexity,
    chars_to_tokens,
)


_NOISE_PREFIXES = (
    "<task-notification>",
    "<task-id>",
    "<local-command",
    "<command-name>",
)
_NOISE_RE = re.compile(
    r"(?is)^\s*(?:<task-notification>|<task-id>|<local-command)"
)
_CONTINUATION_RE = re.compile(r"session is being continued", re.I)

_SESSIONS_ROOT = Path.home() / ".pi" / "agent" / "sessions"


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


def _extract_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                btype = block.get("type")
                if btype == "text":
                    parts.append(str(block.get("text") or ""))
                elif btype in {"tool_result", "toolResult"}:
                    continue
        return "\n".join(p for p in parts if p)
    return ""


def _prompt_quality(text: str) -> float:
    t = (text or "").strip()
    if len(t) < 8:
        return -1e12
    if _NOISE_RE.search(t[:240]):
        return -1e12
    low = t.lower()
    if any(low.startswith(p) for p in _NOISE_PREFIXES):
        return -1e12
    if len(t) < 80 and re.match(
        r"^(continue|conyinue|go on|keep going|yes|ok|retry|run it)\b", low
    ):
        return -1e11
    score = float(len(t))
    if _CONTINUATION_RE.search(t[:400]):
        score *= 0.05
    head = t[:120]
    if "PLATFORM PROMPT" in head or t.lstrip().startswith("# PLATFORM"):
        score += 80_000
    if re.match(r"^(generate|build|create|implement|design)\b", low):
        score += 25_000
    if "## " in t[:800] or "acceptance" in low[:2000]:
        score += 8_000
    if (
        "task_games_" in low
        or "paste this into pi" in low
        or "frostborne" in low
        or "minesweeper" in low
    ):
        score += 15_000
    if low.lstrip().startswith("# ") and len(t) > 200:
        score += 20_000
    return score


def _usage_pair(usage: dict[str, Any]) -> tuple[int, int]:
    """Pi uses input/output; some providers use *_tokens."""
    tin = int(
        usage.get("input_tokens")
        or usage.get("prompt_tokens")
        or usage.get("input")
        or 0
    )
    tout = int(
        usage.get("output_tokens")
        or usage.get("completion_tokens")
        or usage.get("output")
        or 0
    )
    tin += int(usage.get("cache_read_input_tokens") or 0)
    tin += int(usage.get("cache_creation_input_tokens") or 0)
    return tin, tout


def _usage_trustworthy(
    api_tokens: int, est_tokens: int, hits: int, total_msgs: int
) -> bool:
    if total_msgs <= 0 or hits <= 0:
        return False
    if hits < max(2, (total_msgs + 1) // 2):
        if est_tokens > 0 and api_tokens >= int(est_tokens * 0.5):
            return True
        return False
    if est_tokens > 2000 and api_tokens < int(est_tokens * 0.25):
        return False
    return True


def _tool_result_chars(content: Any) -> int:
    if not isinstance(content, list):
        return 0
    n = 0
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") not in {"tool_result", "toolResult"}:
            continue
        raw = block.get("content") if "content" in block else block.get("output")
        if isinstance(raw, str):
            n += len(raw)
        else:
            try:
                n += len(json.dumps(raw, ensure_ascii=False))
            except (TypeError, ValueError):
                n += len(str(raw or ""))
    return n


def analyze_pi_session_file(path: Path) -> dict[str, Any] | None:
    """Return one stats blob for a Pi session JSONL, or None if empty."""
    first_ts: datetime | None = None
    last_ts: datetime | None = None
    prompt_candidates: list[tuple[float, int, str, datetime | None]] = []
    tool_calls = 0
    assistant_messages = 0
    output_chars = 0
    user_chars = 0
    tool_result_chars = 0
    input_tokens = 0
    output_tokens = 0
    usage_hits = 0
    cwd = None
    session_id = path.stem
    if "_" in path.stem:
        session_id = path.stem.rsplit("_", 1)[-1]
    user_idx = 0
    model_votes: dict[str, int] = {}
    model_slices: dict[str, dict[str, Any]] = {}
    current_model: str | None = None

    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue

                rtype = row.get("type")
                ts = _parse_ts(row.get("timestamp"))
                if ts:
                    first_ts = first_ts or ts
                    last_ts = ts

                if rtype == "session":
                    session_id = str(row.get("id") or session_id)
                    cwd = cwd or row.get("cwd")
                    continue

                if rtype == "model_change":
                    mid = str(row.get("modelId") or "").strip()
                    if mid:
                        current_model = mid
                        model_votes[mid] = model_votes.get(mid, 0) + 1
                    continue

                if rtype != "message":
                    continue

                msg = row.get("message")
                if not isinstance(msg, dict):
                    continue
                role = msg.get("role")
                if role == "user":
                    tool_result_chars += _tool_result_chars(msg.get("content"))
                    text = _extract_text(msg.get("content")).strip()
                    user_chars += len(text)
                    if len(text) >= 8:
                        q = _prompt_quality(text)
                        if q > -1e11:
                            prompt_candidates.append(
                                (q + max(0, 500 - user_idx * 15), user_idx, text, ts)
                            )
                        user_idx += 1
                    continue

                if role != "assistant":
                    continue

                assistant_messages += 1
                usage = msg.get("usage") or {}
                tin, tout = _usage_pair(usage if isinstance(usage, dict) else {})
                if tin or tout:
                    usage_hits += 1
                input_tokens += tin
                output_tokens += tout

                raw_model = str(msg.get("model") or current_model or "").strip()
                model = raw_model if raw_model and raw_model != "<synthetic>" else None
                if model:
                    current_model = model
                    model_votes[model] = model_votes.get(model, 0) + 1
                    sl = model_slices.setdefault(
                        model,
                        {
                            "model": model,
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "usage_hits": 0,
                            "assistant_messages": 0,
                            "tool_calls": 0,
                            "output_chars": 0,
                            "first_ts": None,
                            "last_ts": None,
                        },
                    )
                    sl["input_tokens"] += tin
                    sl["output_tokens"] += tout
                    if tin or tout:
                        sl["usage_hits"] += 1
                    sl["assistant_messages"] += 1
                    if ts:
                        if sl["first_ts"] is None:
                            sl["first_ts"] = ts
                        sl["last_ts"] = ts

                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type")
                    if btype == "text":
                        nch = len(str(block.get("text") or ""))
                        output_chars += nch
                        if model:
                            model_slices[model]["output_chars"] += nch
                    elif btype == "thinking":
                        nch = len(str(block.get("thinking") or ""))
                        output_chars += nch
                        if model:
                            model_slices[model]["output_chars"] += nch
                    elif btype in {"toolCall", "tool_use", "tool_call"}:
                        tool_calls += 1
                        if model:
                            model_slices[model]["tool_calls"] += 1
                        try:
                            blob = json.dumps(
                                block.get("arguments")
                                or block.get("input")
                                or {},
                                ensure_ascii=False,
                            )
                            output_chars += len(blob)
                            if model:
                                model_slices[model]["output_chars"] += len(blob)
                        except (TypeError, ValueError):
                            pass
    except OSError:
        return None

    if not prompt_candidates and assistant_messages == 0:
        return None
    if not prompt_candidates:
        prompt_text = f"Pi session {session_id}"
        prompt_ts = first_ts
    else:
        prompt_candidates.sort(key=lambda x: x[0], reverse=True)
        _q, _i, prompt_text, prompt_ts = prompt_candidates[0]

    runtime = None
    if first_ts and last_ts:
        runtime = max(0.0, (last_ts - first_ts).total_seconds())

    base = analyze_prompt_text(prompt_text)
    metrics = apply_effort_complexity(
        base,
        runtime_seconds=runtime,
        tool_calls=tool_calls,
        output_chars=output_chars,
        assistant_messages=assistant_messages,
    )

    out_tok_est = chars_to_tokens(output_chars)
    turns = max(1, assistant_messages)
    transcript_tok = chars_to_tokens(user_chars + tool_result_chars + output_chars)
    in_tok_est = max(
        chars_to_tokens(len(prompt_text)),
        (transcript_tok * turns) // 2,
    )
    trust_usage = _usage_trustworthy(
        output_tokens + input_tokens,
        out_tok_est + in_tok_est,
        usage_hits,
        assistant_messages,
    )

    primary_model = None
    if model_votes:
        primary_model = max(model_votes.items(), key=lambda kv: kv[1])[0]

    breakdown = []
    for model, sl in model_slices.items():
        ft, lt = sl.get("first_ts"), sl.get("last_ts")
        rt = None
        if isinstance(ft, datetime) and isinstance(lt, datetime):
            rt = max(0.0, (lt - ft).total_seconds())
        sl_out_est = chars_to_tokens(sl["output_chars"])
        sl_turns = max(1, sl["assistant_messages"])
        share = sl_turns / max(1, turns)
        sl_in_est = int(in_tok_est * share)
        saw = _usage_trustworthy(
            sl["input_tokens"] + sl["output_tokens"],
            sl_out_est + sl_in_est,
            int(sl.get("usage_hits") or 0),
            sl_turns,
        )
        breakdown.append(
            {
                "model": model,
                "input_tokens": sl["input_tokens"] if saw else None,
                "output_tokens": sl["output_tokens"] if saw else None,
                "input_tokens_est": None if saw else sl_in_est,
                "output_tokens_est": None if saw else sl_out_est,
                "tokens_are_estimated": not saw,
                "runtime_seconds": round(rt, 1) if rt is not None else None,
                "tool_calls": sl["tool_calls"],
                "assistant_messages": sl["assistant_messages"],
                "event_time": ft.isoformat() if isinstance(ft, datetime) else None,
            }
        )

    title = prompt_text.splitlines()[0].lstrip("# ").strip()[:120]
    return {
        "session_id": str(session_id),
        "project": str(cwd or ""),
        "title": title,
        "seed": prompt_text if len(prompt_text) < 6000 else prompt_text[:6000],
        "event_time": (prompt_ts or first_ts or last_ts).isoformat()
        if (prompt_ts or first_ts or last_ts)
        else None,
        "runtime_seconds": round(runtime, 1) if runtime is not None else None,
        "tool_calls": tool_calls,
        "assistant_messages": assistant_messages,
        "output_chars": output_chars,
        "input_tokens": input_tokens if trust_usage else None,
        "output_tokens": output_tokens if trust_usage else None,
        "input_tokens_est": in_tok_est,
        "output_tokens_est": out_tok_est,
        "total_tokens_est": in_tok_est + out_tok_est,
        "tokens_are_estimated": not trust_usage,
        "metrics": metrics,
        "session_path": str(path),
        "model": primary_model,
        "models_seen": sorted(model_votes.keys()),
        "model_breakdown": breakdown,
        "agent": "pi",
    }


def collect_pi_sessions() -> int:
    """Scan ~/.pi/agent/sessions transcripts and upsert ledger rows."""
    from prompt_stats.hooks import build_session_records
    from prompt_stats.ledger import iter_records, rewrite_ledger

    if not _SESSIONS_ROOT.is_dir():
        return 0

    kept = [
        r
        for r in iter_records()
        if r.get("source") not in {"pi_session", "pi_model"}
    ]
    fresh: list[dict[str, Any]] = []
    n = 0
    for path in _SESSIONS_ROOT.rglob("*.jsonl"):
        try:
            if path.stat().st_size < 400:
                continue
        except OSError:
            continue
        stats = analyze_pi_session_file(path)
        if not stats:
            continue
        rt = stats.get("runtime_seconds") or 0
        tools = stats.get("tool_calls") or 0
        asst = stats.get("assistant_messages") or 0
        if rt < 15 and tools < 1 and asst < 1:
            continue
        title = (stats.get("title") or "").strip().lower()
        if title.startswith("<task-notification") or title.startswith("<task-id"):
            continue
        fresh.extend(build_session_records(stats, agent="pi"))
        n += 1
    rewrite_ledger(kept + fresh)
    return n
