# Project Guide — Headless Harness

This document explains the headless harness project in plain language. It is meant for someone who needs to understand what the system is for, how the pieces fit together, and what each major component is responsible for. It deliberately avoids code snippets and command listings. For setup commands and flags, use the repository README. For operator handover and file-layout warnings, use the handover guide. For offline log analysis details, use the debugger guide.

---

## What this project is

The headless harness is an autonomous software-generation system. A human provides a high-level objective in natural language, such as building a web application or a small API. The system then drives a coding agent backend through planning, implementation, verification, and repair until the work either succeeds under strict evidence rules or stops for a clear, recorded reason.

The coding brain is not this Python repository alone. The heavy lifting of reading files, writing code, spawning specialized subagents, and holding long conversation context belongs to Chakra, a gRPC coding agent runtime that lives under the harness directory. This repository surrounds Chakra with a supervisor: it starts one long conversation, approves or denies tools according to safety and phase rules, watches for lifecycle milestones, nudges the agent when the pipeline stalls, records a complete trace of what happened, and decides when the run is finished.

The point of that split is deliberate. Earlier designs tried to make Python an active multi-stage workflow engine that opened separate sessions for generation, verification, and repair. That fought the natural shape of the agent runtime, duplicated orchestration logic, and made context harder to manage. The current design treats Chakra as the owner of the engineering loop and Python as a transparent execution supervisor with hard gates, telemetry, and recovery policy.

---

## The core idea

Autonomous coding fails in predictable ways: the agent explores forever without planning; it writes files in the main turn without finishing environment and status markers; it declares success after reading source without running anything; it wanders outside the assigned project directory; it retries the same denied shell command; or it soft-continues while nothing meaningful for the pipeline advances.

This project encodes answers to those failure modes. Success is not “the assistant said it was done.” Success is an authoritative verification verdict from the verification subagent, accompanied by a runtime check that proves a real build or smoke run. Implementation is not “some files appeared.” Implementation is complete when the general-purpose agent emits the implementation status marker after preparing a project-local environment. Verification is not allowed before that marker. Repair is not optional chatter after a failure; it is a steered loop of repair planning, repair implementation, and re-verification, bounded by a repair iteration limit.

Python never pretends to be the author of the repository. It does not spawn Plan or verification agents by calling the backend as if it were writing the agent’s next thought. It steers by resume messages, tool approval policy, and eventual termination with a causal reason. That keeps Chakra’s conversation as the single source of truth for what the agent decided to do, while still letting the harness enforce contracts the agent alone would violate.

---

## End-to-end flow

A run begins when an operator invokes the production entry point with an objective and optional work directory and run identity. The harness prepares or reuses a project folder under experiments, builds a unified bootstrap prompt that describes the full lifecycle and repository rules, connects to Chakra, and starts one conversation bound to that working directory.

Inside that conversation, Chakra is expected to move through phases. Early work may use Explore to inspect the empty or existing tree, but the pipeline proper starts when Plan produces a plan document. Implementation is supposed to happen through a general-purpose agent that creates and activates a project-local environment, implements against the plan, and emits environment and implementation status markers. Only then should verification run. The verifier must activate the environment, run build and tests or a smoke path, record command evidence, emit a runtime check, and only then emit a pass verdict. If verification fails or a pass is rejected for missing evidence, the conversation should plan a repair, apply it through general-purpose work, mark repair complete, and verify again.

Throughout, Python streams events, auto-approves safe in-repository tools, denies dangerous or out-of-bound actions, updates lifecycle telemetry, and after each turn without completion may send a phase-specific resume nudge instead of a generic “continue.” If the conversation stalls without workflow milestones, recovery logic escalates with stronger messages and execution policy changes—for example denying further Explore spawns until a plan exists. After a configured number of recoveries without real pipeline advance, the run terminates with a reason such as stuck in explore or no forward progress.

When the run ends, artifacts are written under a logs folder named by run identity: a human-readable report, a structured verdict, a summary with lifecycle snapshot, and dual-channel traces. Those traces can later be analyzed offline by the debugger without touching Chakra or the experiment repository.

---

## Roles: Chakra versus Python

Chakra owns the model’s reasoning, tool use, subagent prompts, and conversation memory. It is responsible for deciding when to spawn Plan, Explore, general-purpose, or verification agents, subject to what the harness allows. It also owns context compaction: as the window fills, older tool results and turns may be compacted so long runs can continue without immediately overflowing the model context.

Python owns connection and session lifecycle from the outside, tool intervention responses, supervision policy for completion modes, orchestration state and lifecycle observation, resume nudges, recovery selection and effects, session health timers, phase budgets, workspace confusion tracking, tracing, and final artifact packaging. Python also owns the offline debugger that reads those artifacts after the fact.

This division matters when debugging. If the agent never plans, look at both Chakra behavior and whether Explore exit and recovery fired. If verification passed wrongly, look at the verification parser and prompts. If the process crashed while logging recovery, look at the trace serializer. If the run died for inactivity, look at session health configuration rather than the plan file.

---

## Production entry and bootstrap

The production entry point is the thin outer shell of a run. It parses the objective and limits, ensures a git-backed project directory exists where needed, loads environment configuration, constructs the unified pipeline objective text, creates the Chakra harness adapter and execution engine, wraps them in the conversation runner with a supervisor policy, and after the runner returns saves pipeline artifacts.

The bootstrap message is not a casual user chat line. It is a carefully structured objective that embeds repository boundary rules, execution order for local environments, dependency manifest rules that forbid version pins, subagent spawn expectations, and the verify-repair loop. That text is how Chakra learns the contract for the entire run without Python micromanaging each stage as a separate session.

---

## Conversation runner

The conversation runner is the live heart of supervision. It starts one conversation, registers an observer for engine notifications, installs an intervention handler for tool approvals, streams turns, and loops until completion, health termination, turn or decision limits, or a causal recovery terminate.

On each backend turn it sends either the bootstrap message or a resume message. After a turn completes without a terminal success marker, it updates phase budgets, counts a resume cycle for progress tracking, may select a recovery action, and otherwise asks orchestration for a phase-aware resume nudge. Every decision can be logged as a controller decision so later analysis can see whether the harness soft-continued, nudged, recovered, or terminated.

The runner is intentionally event-driven. It does not poll Chakra with a separate decide-loop LLM for “what stage are we in” as the primary production path. Stage awareness comes from observing tool events and text markers in the same conversation Chakra is already running.

---

## Orchestration state and lifecycle observation

Orchestration state sits between raw events and higher-level decisions. It applies notifications into a coherent picture: which agents started, what they completed, what markers appeared, whether an authoritative verification result was accepted, how many repairs have completed, and whether the main assistant wrote files without going through general-purpose completion markers.

The lifecycle observer is stricter than naive string matching. Verdicts only count as authoritative when they come from a verification subagent completion. Main-assistant prose that says “VERDICT: PASS” does not complete the run. Passes without a runtime check are recorded as rejected and counted toward repair pressure. Implementation complete is not inferred from the mere presence of Write tools; it requires the implementation status marker from the appropriate agent path. Main-agent writes are still counted as telemetry so the debugger and resume logic can notice “files appeared without completion markers” and steer toward general-purpose finishing work.

That lifecycle snapshot feeds resume nudges, phase inference, progress milestones, phase gates, and the final summary written to disk.

---

## Resume nudges

When a turn ends without completion, a generic continue message often lets the model wander. Resume nudges replace that soft continue with a phase-specific instruction when lifecycle state shows a clear gap.

Typical priorities include finishing implementation when a plan exists or writes were seen without completion markers; re-verifying once after a rejected pass if implementation was already complete; escalating to repair planning after a rejected-pass streak or a genuine fail or partial; applying a repair plan via general-purpose when the repair plan file exists; re-running verification after repair complete; and requesting first verification after implementation complete.

Nudges are text. They tell Chakra what to spawn and what markers to emit. They do not themselves open subagent sessions. That keeps the agent runtime in charge of how spawning is expressed, while still making the next required step explicit when the conversation stalls.

---

## Tool approval, intervention guard, and phase gate

Every tool the agent wants to run can trigger an intervention. The harness answers yes or no without calling another LLM for that decision. The intervention guard auto-approves common in-repository engineering tools when paths stay inside the assigned repository root, auto-approves safe agent spawns with allowed subagent types and sensible working directories, and denies empty or echo-only bash, repeated identical bash in a turn, destructive patterns, and paths that leave the repository. Relative parent escapes in bash, such as changing directory upward with parent segments, are treated as out-of-repository style violations so the agent cannot quietly leave the workspace.

After safety approval, additional policy layers apply. The phase gate denies verification or verify subagent spawns until implementation complete has been observed. Recovery may further deny Explore once the harness has decided exploration must end, or deny verification again when implement-first recovery is active. Those denials are recorded with reasons so denial loops and workspace confusion can be detected.

The philosophical stance is that tool approval is stage-aware only through explicit policy modules, not through ad-hoc reading of the user objective inside the approver. Safety stays deterministic; phase policy stays explicit and testable.

---

## Progress tracking versus activity

A central lesson from failed runs is that busyness is not progress. Unique file reads, shell listings, explore completions, and even file writes can keep a naive stall detector happy while the pipeline never reaches plan, implementation complete, or verification.

Progress tracking therefore separates activity telemetry from workflow progress. Activity still increments useful counters for metrics and phase tool or read budgets. Workflow progress that resets the stall counter is reserved for phase transitions and completed milestones: plan presence or plan agent seen, environment ready, implementation complete, repair complete, and accepted verification outcomes that advance the pipeline. Soft continues and denials alone never count as progress.

The offline debugger uses the same philosophy when scanning traces, so live termination reasons and post-hoc stall reports stay aligned.

---

## Explore exit criteria

Explore is useful for discovering an empty tree, but Explore-only runs are a common failure. The harness defines when exploration has gathered enough information to force a transition toward Plan.

Explore has succeeded in the phase sense once Plan has been spawned or a plan document exists. Explore is ready to leave—and should be forced—when the conversation is still in explore or bootstrap and any of several conditions hold: the Explore agent has completed and enough unique in-repository reads have been seen; the explore phase turn or tool budget warns or exceeds; or workspace confusion has crossed its threshold. When ready, recovery prefers a force-plan-and-implement path and can deny further Explore spawns until planning begins.

That policy exists because waiting forever for the model to “decide” to leave Explore is unreliable, while still wanting enough local reading that Plan is not completely blind.

---

## Recovery and execution policy

Recovery is what happens when the normal nudge path is insufficient: forward progress stalled, denial loops dominate, phase budgets pressure the current phase, explore is stuck, or workspace confusion fires.

Selecting recovery returns a kind, a human reason, a resume message, optional termination reason, and effects. Effects are not decorative. They mutate an execution policy for the rest of the session: denied subagent types, workspace lock flags, and clearing of out-of-repository denial groups after a soft workspace reset so the next attempt is not instantly re-terminated on stale counters.

Ordered recoveries typically prefer workspace reset when confusion dominates, implement-first when plan or writes exist without completion, denial strategy when identical or out-of-repo denials loop, repair planning after verification failure with implementation complete, force plan when explore must end, phase budget messages when budgets warn or exceed, and only then generic stall messaging. After the maximum recovery attempts, termination uses causal reasons rather than a vague timeout story whenever possible.

This is how the harness “changes execution” without spawning agents itself: it changes what tools and subagents will be allowed, what the next user message demands, and when the process must stop.

---

## Workspace confusion

Agents frequently probe absolute paths outside the project, parent directories, or harness and controller source trees. Each such denial can be classified as workspace confusion. After a threshold of such events, recovery issues a soft workspace reset: clear out-of-repository denial groups, lock workspace expectations, and send a resume that restates the absolute repository root and forbids parent escapes and harness reads.

Soft reset does not wipe the experiment repository and does not restart the Chakra conversation. It is a policy and messaging reset aimed at breaking a denial spiral while keeping the same session’s memory of useful in-repo work.

---

## Phase contracts and budgets

Phase inference maps lifecycle and spawn sets onto bootstrap, explore, plan, implementation, verification, or repair. While a phase is current, the harness counts controller turns, tools, and reads against per-phase budgets. There are no per-phase wall-clock timers; global session health still covers inactivity and progress timeouts for hung processes.

When budgets warn or exceed, recovery steers toward the phase’s completion criteria—for explore, that means leaving for Plan; for implementation, finishing markers; for verification, producing an evidenced verdict. After recovery budget is exhausted on an exceeded phase, termination can cite a phase-budget-exceeded reason including the phase name.

Budgets exist to stop infinite soft continuation in a phase that is consuming tools without completing its contract.

---

## Session health

Separate from workflow stall detection, session health watches inactivity, lack of progress on a coarser timer basis, and repeated identical failures. It can warn and then terminate the conversation if the session is medically dead even when phase logic has not yet fired. Those timeouts are environment-configurable and are meant for genuinely hung streams or stuck loops, not as the primary way to enforce plan-implement-verify order.

---

## Verification package

The verification package owns the unified objective prompt text, parsing of verdicts and runtime checks, rejection reasons for inadequate passes, and saving of pipeline reports. Parser rules encode that a pass is illegal without a runtime check and that evidence of real command work is required. Reports and verdict JSON are what operators read first after a run; the lifecycle snapshot inside the summary is what explains whether the harness believed implementation and verification contracts were met.

Verification message builders used by resume nudges restate the same runtime requirements so re-verify and first-verify resumes do not soften the contract.

---

## Tracing

Every serious run should leave a dual-channel trace: a normalized orchestration channel that is pleasant to analyze, and a raw events channel that preserves backend detail. Controller decisions, resume nudges, tool approvals, phase budget events, pipeline metrics, and run completion with termination reason all land in the normalized stream when tracing is enabled.

Trace serialization must accept ordinary JSON types. Recovery effects historically included frozen sets of denied subagent names; those must be converted to lists when written. Without that, a run can crash at the exact moment recovery tries to help—an operational footgun the serializer now guards against.

Working traces under a working subdirectory update during the live run; finalized artifacts appear under the pipeline directory when the run packages results.

---

## Offline debugger

The debugger never starts Chakra and never mutates experiment repositories. It loads a run’s pipeline artifacts, validates lifecycle contracts, builds timelines of agents and tools, diagnoses phase reachability, measures forward-progress stalls with the workflow-only definition, groups denials, inspects controller decisions, assigns a causal failure taxonomy, and emits markdown and JSON reports under a debug subdirectory.

Compare mode places two runs side by side for metrics and controller health. The debugger is the primary way to learn why a habit-tracker-style run died in explore or why verification passed twice and was rejected both times. It turns the supervisor’s telemetry into an explanation.

---

## Adapter, engine, interface, and client layers

Beneath the conversation runner sits a layered harness stack. The interface layer defines the abstract harness contract: connect, session, turn streaming, interventions, and event types. The adapter translates that contract onto Chakra’s gRPC protocol. The execution engine manages conversation state, turn execution, and observers without knowing Chakra specifics. The older client package remains for lower-level and historical phase tests.

These layers exist so tests can substitute an in-memory harness, so protocol knowledge stays centralized, and so the supervisor can depend on stable events rather than raw protobuf details. Production users mostly meet them indirectly through the main entry point, but anyone extending the system needs to know that ConversationRunner talks to the engine, which talks to the harness interface, which is implemented by the Chakra adapter.

---

## Experiments and logs directories

The experiments directory holds generated project workspaces. Each workdir is a real repository the agent was told to treat as the only valid root. Operators should not casually delete active experiment trees they still need; they are the product of the run.

The logs directory holds regenerable telemetry. Local deletion is usually safe. Run identity folders keep one attempt’s traces and reports together. Comparing successive run identities for the same objective is a normal debugging workflow.

---

## Scripts and tests

Scripts are operator and infrastructure helpers: starting Chakra with sensible compaction defaults, smoke-testing subagent registration, running the full real-backend suite, generating protobufs, and small manual query or generation-only entry points. Automated tests live under the tests directory, including lifecycle, phase gate, progress, recovery, debugger, and historical phase validations.

Not every test is on the production path. Phase six style decide-loop controller tests remain useful regression coverage even though production supervision is the conversation runner. Knowing that distinction prevents “cleaning” files that still protect contracts.

---

## Configuration philosophy

Environment variables configure LLM access, gRPC endpoints, turn idle timeouts, session health, repair limits, stall and recovery budgets, workspace confusion thresholds, explore exit read counts, and Chakra compaction or stream idle behavior. Chakra-side changes generally require restarting the Chakra process. Harness-side Python changes apply on the next main invocation.

The example environment file is the checklist for a new machine. Secrets belong only in a private environment file, never in documentation.

---

## What success looks like

A successful full pipeline ends with an authoritative verification pass that includes a runtime check, a generated repository under experiments that actually builds or runs as claimed, and logs that show Plan, implementation markers, verification, and no unresolved contract violations. A successful generation-only run ends on the implementation status marker when verification was intentionally skipped.

A well-failed run is also valuable: it stops with a causal termination reason, leaves traces, and yields a debugger report whose primary failure matches what an operator would conclude by reading the conversation. The harness is designed so that silent soft-continue forever is harder than failing loudly with evidence.

---

## What this project is not

It is not a web UI for monitoring agents. It is not a replacement for Chakra’s model or tool runtime. It is not a Python program that invents repository files without the agent. It does not treat Write tools as automatic implementation complete. It does not use per-phase wall-clock budgets as the main control mechanism. It does not wipe or recreate the experiment tree on workspace confusion. It does not claim that Explore alone advances the pipeline.

Understanding those non-goals prevents feature requests that would reintroduce the old multi-session orchestrator or weaken the evidence rules that make autonomous runs trustworthy.

---

## How to think about extending the system

When adding behavior, ask whether Chakra should decide it inside the conversation or whether Python must enforce it as a contract. Contracts and safety belong in Python gates, parsers, and recovery effects. Creative engineering belongs in Chakra subagents and prompts. Telemetry should be rich enough that the debugger can explain new failure modes without re-running the model.

Keep the single-conversation model unless there is a compelling reason to break it. Keep markers and verdict rules strict. Prefer causal termination over silent limits. Prefer workflow milestones over activity when judging progress. Those principles are the project’s center of gravity.

---

## Related documents

The README is the operational front door: setup, commands, flags, outputs, and troubleshooting tables. The handover guide is for maintainers taking ownership of the tree and avoiding accidental deletions. The debugger guide is for post-run diagnosis. The refactoring document explains why the single-conversation supervisor replaced earlier multi-stage Python control. The architecture reference and development journal preserve deeper contract and historical context. This project guide sits between them as a continuous prose map of the system’s purpose and parts.
