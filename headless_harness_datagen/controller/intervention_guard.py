"""Deterministic fast-path for harness intervention approvals (Phase 8)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from controller.workflow_common import validate_agent_spawn

# Tools auto-approved when confined to the repository.
_AUTO_APPROVE_TOOLS = frozenset(
    {
        "Read",
        "Glob",
        "Grep",
        "Write",
        "Edit",
        "MultiEdit",
        "LS",
        "Find",
        "Tree",
        "Ripgrep",
    }
)

_DESTRUCTIVE_BASH_PATTERNS = (
    re.compile(r"\bsudo\b", re.I),
    re.compile(r"rm\s+-rf\s+[/~]"),
    re.compile(r"rm\s+-rf\s+\S*\s+[/~]"),
    re.compile(r">\s*/dev/(?!null\b)"),
    re.compile(r"\.ssh"),
    re.compile(r"\.aws/credentials"),
)

_AMBIGUOUS_BASH_PATTERNS = (
    re.compile(r"\bcurl\b", re.I),
    re.compile(r"\bwget\b", re.I),
    re.compile(r"\bdocker\b", re.I),
    re.compile(r"\bgit\s+push\b", re.I),
    re.compile(r"\bnc\s", re.I),
    re.compile(r"\bssh\b", re.I),
)

# PRD forbids OS-level package installs; they burn long turns and fail on sandbox.
_PACKAGE_INSTALL_BASH_PATTERNS = (
    re.compile(r"\bchoco\s+(install|upgrade|uninstall)\b", re.I),
    re.compile(r"\bwinget\s+(install|upgrade|uninstall)\b", re.I),
    re.compile(r"\bbrew\s+(install|upgrade|uninstall)\b", re.I),
    re.compile(r"\bapt(-get)?\s+install\b", re.I),
    re.compile(r"\byum\s+install\b", re.I),
    re.compile(r"\bdnf\s+install\b", re.I),
    re.compile(r"\bscoop\s+install\b", re.I),
    re.compile(r"\bpacman\s+-S\b", re.I),
)

_SAFE_BASH_PREFIXES = (
    "ls",
    "find",
    "tree",
    "cat",
    "head",
    "tail",
    "pwd",
    "mkdir",
    "touch",
    "cp",
    "mv",
    "chmod",
    "pip install",
    "pip3 install",
    "python ",
    "python3 ",
    "pytest",
    "flask ",
    "npm install",
    "npm run",
    "node ",
    "grep ",
    "rg ",
    "sed -i",
    "source ",
    ". ",
    "test ",
    "[ ",
    "wc ",
    "sort ",
    "uniq ",
    "diff ",
    "which ",
    "env ",
    "export ",
    "cd ",
    "cargo ",
    "rustc ",
    "bash ",
    "sh ",
    "./",
)


@dataclass(frozen=True)
class InterventionGuardResult:
    """Resolved intervention without LLM."""

    response: str
    reasoning: str
    is_echo_bash: bool = False


# Successful uses of these tools are normal exploration — do not count toward
# "interventions without write" stall cancellation.
_STALL_EXEMPT_TOOLS = frozenset(
    {
        "Read",
        "Glob",
        "Grep",
        "LS",
        "Find",
        "Tree",
        "Ripgrep",
    }
)


@dataclass
class StallTracker:
    """Per-turn counters for intervention stall detection."""

    echo_bash_denials: int = 0
    intervention_count: int = 0
    saw_write_or_edit: bool = False

    echo_denial_threshold: int = 3
    # Was 15 — too low: every auto-approved Read/Bash counted, so explore→stall
    # loops (gRPC cancel spam + denial_loop). Pipeline builds need room to explore.
    intervention_without_write_threshold: int = int(
        os.getenv("HARNESS_STALL_INTERVENTION_THRESHOLD", "80")
    )

    def reset(self) -> None:
        self.echo_bash_denials = 0
        self.intervention_count = 0
        self.saw_write_or_edit = False

    def record(
        self,
        *,
        tool_name: str,
        response: str,
        is_echo_bash: bool,
    ) -> None:
        approved = response.strip().lower().startswith("yes")
        if tool_name in ("Write", "Edit", "MultiEdit"):
            self.saw_write_or_edit = True
        if approved and tool_name in _STALL_EXEMPT_TOOLS:
            return
        # Count denials and non-exempt tools (Bash/Write attempts/etc.)
        self.intervention_count += 1
        if (not approved) and is_echo_bash:
            self.echo_bash_denials += 1

    def should_cancel_turn(self) -> bool:
        if self.echo_bash_denials >= self.echo_denial_threshold:
            return True
        if (
            self.intervention_count >= self.intervention_without_write_threshold
            and not self.saw_write_or_edit
        ):
            return True
        return False


def extract_pending_tool(recent_events: list[dict[str, Any]]) -> tuple[str, dict[str, Any]] | None:
    """Return the tool_started event that triggered the current intervention."""
    for event in reversed(recent_events):
        event_type = event.get("event_type")
        if event_type == "intervention_required":
            continue
        if event_type == "tool_started":
            payload = event.get("payload") or {}
            return str(payload.get("tool_name") or ""), dict(payload.get("arguments") or {})
        break
    return None


def normalize_bash_command(command: str) -> str:
    return " ".join(command.strip().split())


def _strip_cd_prefixes(command: str) -> str:
    remainder = command.strip()
    while True:
        # cd PATH &&  — PATH may be quoted
        match = re.match(
            r"""^cd\s+(?:'[^']+'|"[^"]+"|[^\s;&|]+)(?:\s*&&\s*)""",
            remainder,
            re.I,
        )
        if not match:
            break
        remainder = remainder[match.end() :].strip()
    return remainder


def is_echo_only_bash(command: str) -> bool:
    """True when Bash only prints messages (no file/test side effects)."""
    normalized = command.strip()
    if not normalized:
        return False

    remainder = _strip_cd_prefixes(normalized)

    if not re.match(r"^(echo|printf)\b", remainder, re.I):
        return False

    # Disallow pipes or chained commands beyond echo/printf.
    if re.search(r"[|;&](?!\s*$)", remainder):
        return False
    return True


def is_readonly_listing_bash(command: str) -> bool:
    """True for harmless directory/listing commands (safe to retry on Windows)."""
    remainder = _strip_cd_prefixes(command)
    return bool(
        re.match(
            r"^(ls|dir|pwd|tree|Get-ChildItem|gci|gi)\b",
            remainder,
            re.I,
        )
    )


def is_system_package_install_bash(command: str) -> bool:
    """True for choco/winget/brew/apt installs that are forbidden in datagen."""
    stripped = normalize_bash_command(command).lstrip()
    return any(pattern.search(stripped) for pattern in _PACKAGE_INSTALL_BASH_PATTERNS)


def is_recursive_tree_dump(command: str) -> bool:
    """True for `ls -R` / unpruned `find . -type f` that dump cargo target/."""
    stripped = normalize_bash_command(command).lstrip()
    low = stripped.lower()
    if re.match(r"^ls\s+-r(?:\s+\.)?$", low):
        return True
    if re.match(r"^find\s+\.\s+-type\s+f", low) and "-prune" not in low:
        return True
    return False


def _repo_root(context: dict[str, Any]) -> Path | None:
    working_directory = context.get("working_directory")
    if not working_directory:
        return None
    return Path(working_directory).resolve()


def _path_within_repo(path_str: str, repo: Path) -> bool:
    if not path_str:
        return True
    try:
        candidate = Path(path_str).expanduser()
        if not candidate.is_absolute():
            candidate = (repo / candidate).resolve()
        else:
            candidate = candidate.resolve()
        repo_resolved = repo.resolve()
        return candidate == repo_resolved or repo_resolved in candidate.parents
    except (OSError, ValueError):
        return False


def _extract_paths_from_bash(command: str) -> list[str]:
    paths: list[str] = []
    # Only treat `/foo` as absolute when `/` starts a token. `./smoke.sh`
    # used to match `/smoke.sh` and get denied as outside the repo.
    for token in re.findall(r"(?:^|[\s;|&])(/[^\s'\";|&]+)", command):
        path = token.rstrip("'\"")
        if path in {"/dev/null", "/dev/stdout", "/dev/stderr"}:
            continue
        paths.append(path)
    for token in re.findall(r"(~[^\s'\";|&]*)", command):
        paths.append(token)
    return paths


def _bash_confined_to_repo(command: str, repo: Path) -> bool:
    for pattern in _DESTRUCTIVE_BASH_PATTERNS:
        if pattern.search(command):
            return False

    # Relative parent escapes (cd .., ../paths)
    if re.search(r"\bcd\s+\.\.(\s|$|/|;|&)", command, re.I):
        return False
    if "../" in command or "/.." in command:
        return False

    home = Path.home()
    for path_str in _extract_paths_from_bash(command):
        if path_str.startswith("~") and not path_str.startswith(str(home)):
            return False
        if path_str.startswith("/") and not _path_within_repo(path_str, repo):
            return False

    if re.search(r"\bcd\s+([^\s;&|]+)", command, re.I):
        for match in re.finditer(r"\bcd\s+([^\s;&|]+)", command, re.I):
            target = match.group(1).strip("'\"")
            if target in {".", "./"}:
                continue
            if target.startswith("..") or "/../" in target or target.endswith("/.."):
                return False
            if target.startswith("~") and target != "~":
                expanded = os.path.expanduser(target)
                if not _path_within_repo(expanded, repo):
                    return False
            elif target.startswith("/") and not _path_within_repo(target, repo):
                return False
            elif not target.startswith("/") and not target.startswith("~"):
                # Relative cd target — resolve against repo
                if not _path_within_repo(target, repo):
                    return False
    return True


def _is_safe_bash(command: str, repo: Path) -> bool:
    if not _bash_confined_to_repo(command, repo):
        return False

    for pattern in _AMBIGUOUS_BASH_PATTERNS:
        if pattern.search(command):
            return False

    normalized = normalize_bash_command(command)
    stripped = normalized.lstrip()

    if is_echo_only_bash(command):
        return False

    for prefix in _SAFE_BASH_PREFIXES:
        if stripped.lower().startswith(prefix):
            return True

    # heredoc / redirection file creation inside repo
    if "<<" in command or re.search(r">\s*\S+", command):
        return _bash_confined_to_repo(command, repo)

    return False


def _count_matching_bash(tool_events: list[dict[str, Any]], command: str) -> int:
    target = normalize_bash_command(command)
    count = 0
    for event in tool_events:
        if event.get("event_type") != "tool_started":
            continue
        payload = event.get("payload") or {}
        if payload.get("tool_name") != "Bash":
            continue
        args = payload.get("arguments") or {}
        if normalize_bash_command(str(args.get("command") or "")) == target:
            count += 1
    return count


def _count_listing_bash(tool_events: list[dict[str, Any]]) -> int:
    count = 0
    for event in tool_events:
        if event.get("event_type") != "tool_started":
            continue
        payload = event.get("payload") or {}
        if payload.get("tool_name") != "Bash":
            continue
        args = payload.get("arguments") or {}
        cmd = str(args.get("command") or "")
        if is_readonly_listing_bash(cmd) or is_recursive_tree_dump(cmd):
            count += 1
    return count


def _count_matching_read(tool_events: list[dict[str, Any]], file_path: str) -> int:
    target = str(file_path or "").strip().lower()
    if not target:
        return 0
    count = 0
    for event in tool_events:
        if event.get("event_type") != "tool_started":
            continue
        payload = event.get("payload") or {}
        if payload.get("tool_name") != "Read":
            continue
        args = payload.get("arguments") or {}
        src = str(args.get("file_path") or args.get("path") or "").strip().lower()
        if src == target:
            count += 1
    return count


def _count_tool_starts(tool_events: list[dict[str, Any]], names: set[str]) -> int:
    want = {n.lower() for n in names}
    count = 0
    for event in tool_events:
        if event.get("event_type") != "tool_started":
            continue
        payload = event.get("payload") or {}
        name = str(payload.get("tool_name") or "").strip().lower()
        if name in want:
            count += 1
    return count


def _tool_paths_within_repo(tool_name: str, arguments: dict[str, Any], repo: Path) -> bool:
    if tool_name == "Read":
        return _path_within_repo(str(arguments.get("file_path") or ""), repo)
    if tool_name in ("Write", "Edit", "MultiEdit"):
        for key in ("file_path", "path", "target_file"):
            if key in arguments and not _path_within_repo(str(arguments[key]), repo):
                return False
        return True
    if tool_name == "Glob":
        target = str(arguments.get("target_directory") or arguments.get("path") or "")
        return not target or _path_within_repo(target, repo)
    if tool_name == "Grep":
        target = str(arguments.get("path") or "")
        return not target or _path_within_repo(target, repo)
    return True


def evaluate_intervention_guard(context: dict[str, Any]) -> InterventionGuardResult | None:
    """
    Return a deterministic intervention decision, or None to defer to the LLM.

    Auto-approves in-repo engineering tools; auto-denies noop echo bash and repeats.
    """
    pending = extract_pending_tool(context.get("recent_events") or [])
    if pending is None:
        return None

    tool_name, arguments = pending
    repo = _repo_root(context)
    if repo is None:
        return None

    if tool_name in _AUTO_APPROVE_TOOLS:
        pipeline = os.environ.get("DATAGEN_PIPELINE_MODE", "").strip() == "1"
        tool_events = context.get("tool_events") or []
        if tool_name == "Read" and pipeline:
            file_path = str(arguments.get("file_path") or arguments.get("path") or "")
            low = file_path.replace("\\", "/").lower()
            if low.endswith("/platform_prompt.md"):
                # tool_events usually already includes the pending Read, so
                # threshold 1 wrongly blocked the first PRD read on CONTINUE.
                seen = _count_matching_read(tool_events, file_path)
                if seen >= 2:
                    return InterventionGuardResult(
                        response="no",
                        reasoning=(
                            "deny repeated platform_prompt.md reads in pipeline — "
                            "start Write/Edit now"
                        ),
                    )
            writes = _count_tool_starts(
                tool_events, {"Write", "Edit", "MultiEdit"}
            )
            reads = _count_tool_starts(tool_events, {"Read"})
            # After a Read binge with zero writes, block further Read so the
            # model must Write (or burn turns on empty replies / denials).
            if writes == 0 and reads >= 8:
                return InterventionGuardResult(
                    response="no",
                    reasoning=(
                        "deny Read during write starvation — "
                        "REQUIRED next tool: Write scripts/smoke.py (or source)"
                    ),
                )
        if _tool_paths_within_repo(tool_name, arguments, repo):
            return InterventionGuardResult(
                response="yes",
                reasoning=f"auto-approve in-repo {tool_name}",
            )
        return InterventionGuardResult(
            response="no",
            reasoning=f"deny {tool_name} outside repository boundary",
        )

    if tool_name == "Agent":
        if os.environ.get("DATAGEN_PIPELINE_MODE", "").strip() == "1":
            return InterventionGuardResult(
                response="no",
                reasoning="deny Agent in datagen pipeline (Write/Edit only; no Plan/Explore)",
            )
        ok, reason = validate_agent_spawn(arguments, repo_path=repo)
        if ok:
            return InterventionGuardResult(
                response="yes",
                reasoning=f"auto-approve {reason}",
            )
        return InterventionGuardResult(
            response="no",
            reasoning=reason,
        )

    if tool_name == "Bash":
        command = str(arguments.get("command") or "")
        if not command.strip():
            return InterventionGuardResult(
                response="no",
                reasoning="deny empty Bash command",
            )

        if is_echo_only_bash(command):
            return InterventionGuardResult(
                response="no",
                reasoning="deny echo-only Bash (completion must be assistant text, not shell output)",
                is_echo_bash=True,
            )

        if is_system_package_install_bash(command):
            return InterventionGuardResult(
                response="no",
                reasoning="deny system package manager install (use Read/ls on src/; no choco/winget/brew)",
            )

        # ls -R / find dumps are rewritten to safe listings in Chakra gRPC
        # (slimBashCommand). Approve here so the rewrite can run.
        if is_recursive_tree_dump(command):
            if _is_safe_bash(command, repo):
                return InterventionGuardResult(
                    response="yes",
                    reasoning="approve tree listing (Chakra gRPC rewrites ls -R/find to skip target/)",
                )

        repeats = _count_matching_bash(context.get("tool_events") or [], command)
        listing_n = _count_listing_bash(context.get("tool_events") or [])
        pipeline = os.environ.get("DATAGEN_PIPELINE_MODE", "").strip() == "1"
        if pipeline and (
            is_readonly_listing_bash(command) or is_recursive_tree_dump(command)
        ):
            # gpt spends entire max_turns on ls -la / Read loops.
            if listing_n >= 2:
                return InterventionGuardResult(
                    response="no",
                    reasoning=(
                        "deny further listing in datagen pipeline — "
                        "Write fixtures/seed.json and scripts/smoke.py now"
                    ),
                )
        # Listing commands often fail once on Windows (ls vs dir) and get retried;
        # denying them causes denial_loop termination with zero backend progress.
        if repeats >= 2 and not is_readonly_listing_bash(command):
            return InterventionGuardResult(
                response="no",
                reasoning="deny repeated identical Bash command in this turn",
            )

        if not _bash_confined_to_repo(command, repo):
            return InterventionGuardResult(
                response="no",
                reasoning="deny Bash outside repository or destructive pattern",
            )

        if _is_safe_bash(command, repo):
            return InterventionGuardResult(
                response="yes",
                reasoning="auto-approve safe in-repo Bash",
            )

        return None

    return None
