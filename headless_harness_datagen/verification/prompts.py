"""Unified pipeline objective prompt for the Phase 7 conversation."""

from __future__ import annotations

from pathlib import Path


SANDBOX_ENVIRONMENT_INSTRUCTIONS = """=== REPOSITORY EXECUTION POLICY (MANDATORY) ===
The following rules govern repository execution. These rules are mandatory.
==================================================
A. REPOSITORY BOUNDARIES
==================================================
The assigned Repository Root is the ONLY valid workspace.
Every project file, source file, configuration file, dependency,
execution environment, generated artifact, build output, test output,
repair, and runtime operation MUST remain inside this repository.
Never:
• create a repository outside the assigned Repository Root
• relocate the repository
• continue implementation inside another repository
• search the filesystem for an alternative project
• switch to another existing project
• modify unrelated repositories
• modify unrelated directories
• create project files outside the repository
• install dependencies globally
• execute project commands outside the repository
• reuse execution environments from another project
If the assigned repository already exists:
• continue working inside it
If repository creation fails because the directory already exists:
• remain inside the assigned parent directory
• create a uniquely named sibling directory
• never relocate the project
If files were accidentally created outside the assigned repository:
• stop working outside the repository
• move or recreate the required files inside the assigned repository
• continue all remaining work only inside the assigned repository
The repository must never leave the assigned Repository Root.
==================================================
B. REQUIRED EXECUTION ORDER
The following workflow is mandatory.
1. Verify whether the assigned repository exists.
2. If it does not exist, create it.
3. Enter the repository.
4. Verify that the current working directory exactly matches the assigned Repository Root.
5. Determine whether a project-local execution environment already exists.
6. If no environment exists:
• create one
• activate it
• verify activation
If an environment already exists:
• activate it
• verify activation
7. Only after the execution environment is active may dependencies be installed.
8. Only after dependency installation may project commands execute.
Never change this execution order.
==================================================
C. EXECUTION ENVIRONMENT
Every repository MUST own its own isolated execution environment.
Never:
• use the host environment
• install dependencies globally
• execute project commands outside the activated environment
• reuse another repository's environment
Every build, test, compilation, execution and repair must occur inside
the activated project environment.
==================================================
D. TECHNOLOGY DETECTION
Automatically determine the project's technology stack.
Use the standard project-local workflow for the detected ecosystem.
Examples include:
• Python (.venv)
• Node.js / TypeScript (local node_modules)
• Rust (Cargo)
• Go (Go Modules)
• Java (Gradle Wrapper / Maven Wrapper)
For every other language or framework,
automatically determine the appropriate local workflow.
==================================================
E. GENERAL EXECUTION RULES
Every dependency installation must occur inside the repository.
Every build must occur inside the repository.
Every compilation must occur inside the repository.
Every automated test must occur inside the repository.
Every runtime command must occur inside the repository.
Every repair must occur inside the repository.
Every generated execution environment belongs only to this repository.
Environment directories should not be committed unless explicitly required.
==================================================
F. DEPENDENCY MANIFESTS (MANDATORY)
List package/crate/module names; do not pin exact versions or hashes.
For ecosystems that require a version field, use a wildcard / latest:
• Python requirements.txt: `fastapi` (name only, no versions)
• Cargo.toml: `tiny_http = "*"`  (never `tiny_http = "tiny_http"`)
• package.json: `"express": "*"`
Wrong: fastapi==0.115.0 / "express": "^4.18.0" / tiny_http = "0.12"
Never pin versions to concrete releases.
==================================================
G. FAILURE RECOVERY
If any engineering step fails:
• determine the cause
• repair the repository
• repeat the failed step
• continue execution
Never abandon the repository after the first failure.
Never ignore failed engineering steps.
Continue until the repository succeeds or the repair budget is exhausted —
do not polish indefinitely after a green smoke test.
==================================================
H. SUBAGENT SPAWN RULES
Prefer setting cwd to the absolute Repository Root on every Agent spawn.
isolation="worktree" is allowed when the worktree is of this Repository Root
(prefer cwd="{repo}" so the worktree anchors correctly). Never use
isolation="remote". Never place project files outside the Repository Root.
On Agent tool calls: OMIT the model field (or set model="inherit").
Never pass model="sonnet"/"opus"/"haiku" — those break OpenAI-compatible proxies.
"""


SPEED_BUDGET_INSTRUCTIONS = """=== SPEED / TIME BUDGET (MANDATORY) ===
Hour-long runs are a failure mode. Target a working MVP in well under 25 minutes
of agent wall time.

1. Batch work: emit multiple Write/Edit tools in ONE response whenever possible.
   Never write one tiny file per turn.
2. Prefer small local dependencies. Do NOT download torch/cuda, Unity Hub, or
   other multi-GB packages unless the objective explicitly requires them AND
   they are already installed (import / which succeeds).
3. If a heavy package is already importable, skip pip/npm reinstall.
4. Tests: run a fast unit/smoke suite only. Do not loop on pytest -m slow,
   full ImageNet downloads, or end-to-end suites that take >2 minutes.
5. Never winget/choco install IDEs, Unity, or system runtimes mid-run.
   If the toolchain is missing, implement source + docs + the closest runnable
   fallback (e.g. browser prototype for Unity) and stop after smoke green.
6. Do not print IMPLEMENTATION_STATUS COMPLETE until README.md, a smoke script,
   and fixtures/ or data/ seed files exist. Extra polish after a shippable demo is optional.
7. Keep plans short (plan.md ≤ ~80 lines). Prefer shipping over exhaustive PRDs.
8. If cargo/link/dlltool fails once on Windows, do not loop the compiler — keep
   source plus a best-effort smoke that proves the demo as far as the toolchain allows.
==================================================
"""


def write_harness_policy_file(repo_dir: str | Path) -> Path:
    """Write full execution policy to the repo. Do not inline it in LLM requests."""
    repo = Path(repo_dir)
    path = repo / "HARNESS_POLICY.md"
    sandbox = SANDBOX_ENVIRONMENT_INSTRUCTIONS.replace("{repo}", str(repo))
    path.write_text(
        "# Harness execution policy\n\n"
        "This file is staged on disk because inlining it in ChatRequest "
        "times out the OpenAI-compatible proxy (0 tokens).\n"
        "Read it once if you need repo/env rules.\n\n"
        f"{SPEED_BUDGET_INSTRUCTIONS}\n{sandbox}\n",
        encoding="utf-8",
    )
    return path


def build_unified_pipeline_objective(
    *,
    repo_path: str,
    objective: str,
    max_repair_iterations: int = 3,
    include_verification: bool = True,
) -> str:
    """
    Bootstrap objective for a single persistent Chakra conversation.

    Keep this short. TensorStudio times out (~5 min, 0 tokens) on the old
    8k-char SANDBOX dump. Full policy lives in HARNESS_POLICY.md in the repo.
    """
    plan_file = f"{repo_path}/plan.md"
    repair_plan_file = f"{repo_path}/repair_plan.md"
    if include_verification:
        return f"""You are the primary Chakra coding agent for an autonomous repository pipeline.
You own the COMPLETE repository generation lifecycle in THIS single conversation.
Python will not start a second session for verification or repair.
Python may send phase-specific resume instructions when verification fails or PASS is rejected. Follow those immediately.

Recommended lifecycle (follow this narrative; you decide when to spawn):
  Write plan.md → implement yourself (Write/Edit/Bash; do NOT spawn Agent) → verification
       ↑                                           │
       │                                     VERDICT: PASS → done
       │                                     VERDICT: FAIL or PARTIAL
       └──── Write repair_plan.md → repair yourself
             then verification again
  Repeat verify↔repair at most {max_repair_iterations} times.

Required steps:
1. Plan — Write {plan_file} yourself (Plan subagent is READ-ONLY). Keep it <=80 lines.
2. Environment + Implement — YOU implement (do NOT spawn Agent/general-purpose):
   a. Create/activate a project-local env (.venv / node_modules / Cargo); reuse if present
   b. DEPENDENCY MANIFESTS: names only / "*" wildcards, Never pin versions, tiny_http = "*"
   c. Batch writes; stop after a green smoke test
   d. Emit ENV_STATUS: READY then IMPLEMENTATION_STATUS: COMPLETE
3. Verify — spawn verification (prefer cwd="{repo_path}") with the original objective.
   Verification MUST activate the project env, run ONE fast smoke, record Command run
   + exit codes, emit RUNTIME_CHECK: PASS only on exit 0. VERDICT: PASS is illegal
   without RUNTIME_CHECK: PASS. Do not PASS on static file review alone.
4. On VERDICT: FAIL or PARTIAL: Write {repair_plan_file} yourself, repair in-repo,
   emit REPAIR_STATUS: COMPLETE, then spawn verification again.
5. Stop on VERDICT: PASS with RUNTIME_CHECK: PASS (or after {max_repair_iterations} rounds).

Do not spawn verification before IMPLEMENTATION_STATUS: COMPLETE.
Available subagents: general-purpose, verification, Explore.
Only the verification subagent may issue VERDICT: PASS, FAIL, or PARTIAL.
Do not self-assign a verdict.
Do not ask the harness to start a second conversation.
Treat repair and re-verification as ordinary work in this same conversation.
On Agent calls omit model (or model="inherit"). Never model=sonnet/opus/haiku.
isolation="worktree" is allowed when the worktree is of Repository Root {repo_path}; never isolation="remote".

Repository Root: {repo_path}
Read HARNESS_POLICY.md once for repo/env rules. Read platform_prompt.md once, then implement.

PROJECT OBJECTIVE
{objective}

The conversation is complete only when the verification subagent returns VERDICT: PASS together with RUNTIME_CHECK: PASS.
"""
    return (
        f"Repo: {repo_path}\n"
        f"Read platform_prompt.md once, then Write/Edit until the demo works.\n"
        f"Do not run verification. Do not spawn Agent/Plan/Explore.\n"
        f"Do not loop ls or cargo. Names-only deps. Never pin versions. No package installs.\n"
        f"On Agent omit model (or model=\"inherit\").\n"
        f"Do not print IMPLEMENTATION_STATUS: COMPLETE until README.md, "
        f"scripts/smoke.py (or npm run smoke), fixtures/ or data/ seeds, and a working demo exist.\n"
        f"If cargo/dlltool fails once, keep writing source + smoke; do not retry the compiler.\n"
        f"\nOBJECTIVE\n{objective}\n"
    )
