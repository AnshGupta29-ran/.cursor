"""Parse ~/.chakra project session JSONL for real duration + activity."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from prompt_stats.ledger import load_records, upsert_merge
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
                if block.get("type") == "text":
                    parts.append(str(block.get("text") or ""))
                elif block.get("type") == "tool_result":
                    continue
        return "\n".join(p for p in parts if p)
    return ""


def _is_tool_result_user(message: dict[str, Any]) -> bool:
    content = message.get("content")
    if not isinstance(content, list):
        return False
    return any(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in content
    )


def _prompt_quality(text: str) -> float:
    """Rank user messages so we pick the real task, not notifications."""
    t = (text or "").strip()
    if len(t) < 8:
        return -1e12
    if _NOISE_RE.search(t[:240]):
        return -1e12
    low = t.lower()
    if any(low.startswith(p) for p in _NOISE_PREFIXES):
        return -1e12
    # Bare continue/ok nudges must never beat real task pastes
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
        or "frostborne" in low
        or "paste this into" in low
        or "card battler" in low
        or "minesweeper" in low
    ):
        score += 15_000
    if t.lstrip().startswith("# ") and len(t) > 200:
        score += 20_000
    return score


def _usage_pair(usage: dict[str, Any]) -> tuple[int, int]:
    """Normalize provider usage keys (Anthropic / OpenAI / LiteLLM)."""
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
    # Cache tokens are still billed/consumed input context
    tin += int(usage.get("cache_read_input_tokens") or 0)
    tin += int(usage.get("cache_creation_input_tokens") or 0)
    return tin, tout


def _usage_trustworthy(
    api_tokens: int, est_tokens: int, hits: int, total_msgs: int
) -> bool:
    """Reject sparse/partial usage that under-counts vs transcript size."""
    if total_msgs <= 0 or hits <= 0:
        return False
    # One stray usage blob on a long session must not win over char estimates
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
        if block.get("type") != "tool_result":
            continue
        raw = block.get("content")
        if isinstance(raw, str):
            n += len(raw)
        else:
            try:
                n += len(json.dumps(raw, ensure_ascii=False))
            except (TypeError, ValueError):
                n += len(str(raw or ""))
    return n


def analyze_session_file(path: Path) -> dict[str, Any] | None:
    """Return one stats blob for a Chakra session JSONL, or None if empty."""
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
    user_idx = 0
    model_votes: dict[str, int] = {}
    # per-model attribution (tokens + wall span while that model was answering)
    model_slices: dict[str, dict[str, Any]] = {}

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
                ts = _parse_ts(row.get("timestamp"))
                if ts:
                    first_ts = first_ts or ts
                    last_ts = ts
                cwd = cwd or row.get("cwd")
                session_id = row.get("sessionId") or session_id
                msg = row.get("message")
                if not isinstance(msg, dict):
                    continue
                role = msg.get("role")
                if role == "user":
                    tool_result_chars += _tool_result_chars(msg.get("content"))
                    if _is_tool_result_user(msg):
                        continue
                    text = _extract_text(msg.get("content")).strip()
                    user_chars += len(text)
                    if len(text) >= 8:
                        q = _prompt_quality(text)
                        if q > -1e11:
                            # Earlier real prompts get a small boost
                            prompt_candidates.append(
                                (q + max(0, 500 - user_idx * 15), user_idx, text, ts)
                            )
                        user_idx += 1
                elif role == "assistant":
                    assistant_messages += 1
                    usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
                    tin, tout = _usage_pair(usage)
                    if tin or tout:
                        usage_hits += 1
                    input_tokens += tin
                    output_tokens += tout
                    raw_model = str(msg.get("model") or "").strip()
                    model = raw_model if raw_model and raw_model != "<synthetic>" else None
                    if model:
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
                    if isinstance(content, list):
                        for block in content:
                            if not isinstance(block, dict):
                                continue
                            if block.get("type") == "text":
                                nch = len(str(block.get("text") or ""))
                                output_chars += nch
                                if model:
                                    model_slices[model]["output_chars"] += nch
                            elif block.get("type") == "thinking":
                                nch = len(str(block.get("thinking") or ""))
                                output_chars += nch
                                if model:
                                    model_slices[model]["output_chars"] += nch
                            elif block.get("type") == "tool_use":
                                tool_calls += 1
                                if model:
                                    model_slices[model]["tool_calls"] += 1
                                try:
                                    blob = json.dumps(
                                        block.get("input") or {},
                                        ensure_ascii=False,
                                    )
                                    output_chars += len(blob)
                                    if model:
                                        model_slices[model]["output_chars"] += len(blob)
                                except (TypeError, ValueError):
                                    pass
    except OSError:
        return None

    if not prompt_candidates:
        # Still record active sessions (resume / continue-only threads)
        if assistant_messages == 0 and tool_calls == 0:
            return None
        prompt_text = f"Chakra session {session_id}"
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
    # When providers leave usage at 0 (common for some OpenAI-compat proxies),
    # estimate cumulative input via triangle of transcript size × turns
    # (user_chars/tool_result_chars are already full-session totals — do NOT
    # multiply them by turns again as if they were a per-turn seed).
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

    # Attribute leftover output chars (synthetic / untagged turns) to primary
    # so Σ model slices == session output.
    attributed = sum(int(sl.get("output_chars") or 0) for sl in model_slices.values())
    leftover = max(0, output_chars - attributed)
    if leftover and primary_model and primary_model in model_slices:
        model_slices[primary_model]["output_chars"] += leftover

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
        "agent": "chakra",
    }


def _match_keys(text: str) -> set[str]:
    low = (text or "").lower()
    keys = set()
    for k in (
        "tidewatch",
        "palletlens",
        "ecommerce",
        "ecom_test",
        "e-commerce",
        "gaming platform",
        "blogging platform",
        "social media",
        "taskflow",
        "whiteboard",
        "smart home",
        "tower defense",
        "frostborne",
        "minesweeper",
        "card battler",
        "fathom fields",
        "task_games_01",
        "task_games_02",
        "task_games_03",
        "task_games_04",
        "task_games_05",
        "task_games_06",
        "task_games_07",
        "task_games_08",
        "task_games_09",
        "task_games_10",
    ):
        if k in low:
            keys.add(k.replace("-", "").replace("_", "").replace(" ", ""))
    for m in re.finditer(r"task[_ ]?games[_ ]?0?\d+", low):
        keys.add(re.sub(r"[^a-z0-9]", "", m.group(0)))
    # Product-ish Title Case words from forge titles
    for m in re.finditer(r"\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b", text or ""):
        keys.add(m.group(1).lower())
    return keys


def enrich_ledger_from_sessions() -> int:
    """Copy session runtime/tokens/effort complexity onto matching forge/pipeline rows."""
    from prompt_stats.ledger import rewrite_ledger

    records = load_records()
    sessions = [r for r in records if r.get("source") == "chakra_session"]
    if not sessions:
        return 0
    session_keys = [
        (s, _match_keys(f"{s.get('title') or ''} {s.get('seed') or ''}"))
        for s in sessions
    ]
    n = 0
    out: list[dict[str, Any]] = []
    for row in records:
        if row.get("source") in {"chakra_session", "chakra_model", "pi_session", "pi_model"}:
            out.append(row)
            continue
        hay = f"{row.get('title') or ''} {row.get('seed') or ''} {row.get('objective') or ''}"
        keys = _match_keys(hay)
        if not keys:
            out.append(row)
            continue
        best = None
        best_overlap = 0
        for s, sk in session_keys:
            overlap = len(keys & sk)
            if overlap > best_overlap:
                best_overlap = overlap
                best = s
        if not best or best_overlap < 1:
            out.append(row)
            continue
        rt = best.get("runtime_seconds")
        if not isinstance(rt, (int, float)) or rt < 30:
            out.append(row)
            continue
        cur_rt = row.get("runtime_seconds")
        if (
            row.get("linked_session_id") == best.get("session_id")
            and isinstance(cur_rt, (int, float))
            and cur_rt >= rt * 0.95
            and (row.get("output_tokens_est") or row.get("output_tokens"))
            and (row.get("output_tokens_est") or row.get("output_tokens") or 0)
            >= (best.get("output_tokens_est") or best.get("output_tokens") or 0) * 0.9
        ):
            out.append(row)
            continue
        patched = dict(row)
        patched["runtime_seconds"] = rt
        patched["tool_calls"] = best.get("tool_calls")
        patched["linked_session_id"] = best.get("session_id")
        patched["tokens_are_estimated"] = best.get("tokens_are_estimated", True)
        if best.get("input_tokens") is not None:
            patched["input_tokens"] = best["input_tokens"]
        else:
            patched["input_tokens_est"] = best.get("input_tokens_est")
        if best.get("output_tokens") is not None:
            patched["output_tokens"] = best["output_tokens"]
        else:
            patched["output_tokens_est"] = best.get("output_tokens_est")
        if best.get("total_tokens_est") is not None:
            patched["total_tokens_est"] = best["total_tokens_est"]
        for k in (
            "complexity_score",
            "complexity_band",
            "complexity_score_prompt_only",
            "complexity_effort_bonus",
        ):
            if best.get(k) is not None:
                patched[k] = best[k]
        out.append(patched)
        n += 1
    if n:
        rewrite_ledger(out)
    return n


def collect_chakra_sessions() -> int:
    """Scan ~/.chakra/projects session transcripts (all local projects)."""
    from prompt_stats.hooks import build_session_records
    from prompt_stats.ledger import iter_records, rewrite_ledger

    projects = Path.home() / ".chakra" / "projects"
    if not projects.is_dir():
        return 0

    kept = [
        r
        for r in iter_records()
        if r.get("source") not in {"chakra_session", "chakra_model"}
    ]
    fresh: list[dict[str, Any]] = []
    n = 0
    paths = [
        p
        for p in projects.rglob("*.jsonl")
        if not p.name.lower().startswith("agent-")
    ]
    for i, path in enumerate(paths):
        try:
            if path.stat().st_size < 500:
                continue
        except OSError:
            continue
        if i % 5 == 0:
            print(f"  chakra scan {i+1}/{len(paths)} {path.name}", flush=True)
        stats = analyze_session_file(path)
        if not stats:
            continue
        rt = stats.get("runtime_seconds") or 0
        tools = stats.get("tool_calls") or 0
        if rt < 20 and tools < 3:
            continue
        title = (stats.get("title") or "").strip().lower()
        if title.startswith("<task-notification") or title.startswith("<task-id"):
            continue
        stats["agent"] = "chakra"
        fresh.extend(build_session_records(stats, agent="chakra"))
        n += 1
    print(f"  chakra writing {n} sessions ({len(fresh)} rows)", flush=True)
    rewrite_ledger(kept + fresh)
    try:
        en = enrich_ledger_from_sessions()
        print(f"  chakra enriched {en} rows", flush=True)
    except Exception as exc:
        print(f"session enrich skipped: {exc}", flush=True)
    return n
