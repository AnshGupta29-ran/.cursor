# Harness execution policy

This file is staged on disk because inlining it in ChatRequest times out the OpenAI-compatible proxy (0 tokens).
Read it once if you need repo/env rules.

=== SPEED / TIME BUDGET (MANDATORY) ===
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

=== REPOSITORY EXECUTION POLICY (MANDATORY) ===
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
(prefer cwd="C:\Users\anshg\.cursor\headless_harness_datagen\experiments\task_ai_ml_02__v04_python_security-auditor_audit-trail-export" so the worktree anchors correctly). Never use
isolation="remote". Never place project files outside the Repository Root.
On Agent tool calls: OMIT the model field (or set model="inherit").
Never pass model="sonnet"/"opus"/"haiku" — those break OpenAI-compatible proxies.

