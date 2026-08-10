# Enabling Built-in Agents on Chakra gRPC

This is a **Chakra backend change + harness integration** guide. Built-in agents (`verification`, `general-purpose`, `Explore`, `plan`, etc.) exist in Chakra’s CLI/SDK path but are **disabled on the gRPC path** your harness uses today.

---

## Current state

In `harness/chakra/src/grpc/server.ts`, the gRPC `QueryEngine` is created with:

```100:100:harness/chakra/src/grpc/server.ts
            agents: [],
```

With an empty agent list:

- The **`Agent` tool** still exists in `getTools()`, but there are **no `subagent_type` values** to spawn.
- Spawning `subagent_type="verification"` fails with “agent type not found”.
- Your **separate validation controller** (`verification/`) is doing all verifier work instead.

The CLI path loads agents via `getBuiltInAgents()` in `builtInAgents.ts`.

---

## What each built-in agent is for

| Agent | `subagent_type` | Use in harness pipeline |
|-------|-----------------|-------------------------|
| **general-purpose** | `general-purpose` | Offload large multi-file implementation from main thread |
| **verification** | `verification` | Adversarial read-only testing; ends with `VERDICT: PASS/FAIL/PARTIAL` |
| **Explore** | `Explore` | Read-only codebase search (3+ queries) |
| **plan** | `plan` | Read-only architecture / implementation planning |
| **statusline-setup** | (internal) | Not relevant for your pipeline |
| **claude-code-guide** | (internal) | CLI-only helper |

The **verification agent** is the main one for offloading validation behavior. Its prompt and constraints live in `verificationAgent.ts` (read-only, command evidence required, `VERDICT:` line).

---

## Step 1 — Register agents on the gRPC server

### Minimal change (recommended starting point)

In `harness/chakra/src/grpc/server.ts`:

1. Import agent definitions.
2. Replace `agents: []` with an explicit list (most reliable — bypasses feature flags).

Conceptually:

```typescript
import { GENERAL_PURPOSE_AGENT } from '../tools/AgentTool/built-in/generalPurposeAgent.js'
import { VERIFICATION_AGENT } from '../tools/AgentTool/built-in/verificationAgent.js'
import { EXPLORE_AGENT } from '../tools/AgentTool/built-in/exploreAgent.js'
import { PLAN_AGENT } from '../tools/AgentTool/built-in/planAgent.js'

// Inside QueryEngine constructor:
agents: [
  GENERAL_PURPOSE_AGENT,
  VERIFICATION_AGENT,
  EXPLORE_AGENT,
  PLAN_AGENT,
],
```

**Why explicit imports instead of `getBuiltInAgents()`?**

`getBuiltInAgents()` is gated twice:

```64:68:harness/chakra/src/tools/AgentTool/builtInAgents.ts
  if (
    feature('VERIFICATION_AGENT') &&
    getFeatureValue_CACHED_MAY_BE_STALE('tengu_hive_evidence', false)
  ) {
    agents.push(VERIFICATION_AGENT)
```

- `feature('VERIFICATION_AGENT')` — compile-time `bun:bundle` flag; often **false** in `dev:grpc` (runs TS directly, not the built bundle).
- `tengu_hive_evidence` — GrowthBook flag, **defaults to false**.

Explore/plan have similar gates (`BUILTIN_EXPLORE_PLAN_AGENTS` + `tengu_amber_stoat`).

Direct imports avoid both gates.

### Alternative: use `getBuiltInAgents()` + force flags

If you prefer the dynamic loader (also picks up custom agents from `.claude/agents/` via `getAgentDefinitionsWithOverrides`):

```typescript
import { getAgentDefinitionsWithOverrides } from '../tools/AgentTool/loadAgentsDir.js'

const workDir = req.working_directory || process.cwd()
const { activeAgents } = await getAgentDefinitionsWithOverrides(workDir)

engine = new QueryEngine({
  ...
  agents: activeAgents,
})
```

To make verification appear through that path you’d also need:

| Gate | How to enable |
|------|----------------|
| `feature('VERIFICATION_AGENT')` | Add to `harness/chakra/scripts/build.ts` `featureFlags`, or use explicit imports |
| `tengu_hive_evidence` | `USER_TYPE=ant` + `CLAUDE_INTERNAL_FC_OVERRIDES='{"tengu_hive_evidence": true}'` (internal Chakra env), or patch `builtInAgents.ts` |

For your open-source fork, **explicit imports in `server.ts`** are the simplest.

### Restart

Per your README: after editing `grpc/server.ts`, restart Chakra:

```bash
./scripts/start_chakra.sh
```

`dev:grpc` runs source via Bun — no full `bun run build` required for this file.

---

## Step 2 — Make the main agent actually use them

Registering agents is necessary but not sufficient. The main agent must be **told** to spawn subagents.

### What Chakra CLI does automatically

In interactive CLI, when verification is enabled, the system prompt includes a contract like: “after non-trivial work, spawn `Agent` with `subagent_type=verification`…” (`constants/prompts.ts`). That block is gated by the same flags above and by `getIsNonInteractiveSession()` behavior.

On gRPC, you likely **won’t get those nudges** unless flags are on. So you must add instructions from the **harness controller**.

### Generation bootstrap (harness side)

Extend your generation bootstrap message (`controller/completion_guard.py` / `controller/policies.py`) along these lines:

```text
After implementing the PROJECT OBJECTIVE:
1. Spawn Agent with subagent_type="verification".
   Pass: original objective, files changed, approach taken, workdir path.
2. Do NOT self-assign PASS/FAIL — only the verification agent issues VERDICT.
3. On VERDICT: FAIL — fix the repo, then re-spawn verification until PASS.
4. On VERDICT: PASS — spot-check 2–3 commands from the verifier report.
5. Only then report completion to the controller.
```

Optional for large repos:

```text
Before implementation, optionally spawn subagent_type="plan" to produce an implementation plan.
For broad codebase search, use subagent_type="Explore".
For large multi-file edits, delegate to subagent_type="general-purpose".
```

### Completion guard (harness side)

Today `completion_guard.py` blocks premature `complete` based on turn count and objective keywords. You’d extend it to also require:

- Evidence that `Agent` with `verification` was spawned, **or**
- A `VERDICT: PASS` line in recent backend output

Without this, the backend can still “finish” without ever calling the verifier — same problem you saw with early `complete`.

---

## Step 3 — Handle the intervention explosion (critical)

Every tool call on gRPC goes through `canUseTool`, which emits `action_required` and waits for your harness to reply `yes`/`no`:

```103:135:harness/chakra/src/grpc/server.ts
            canUseTool: async (tool, input, ...) => {
              ...
              call.write({ action_required: { ... } })
              return new Promise((resolve) => { ... })
            },
```

When a **verification subagent** runs 20–40 bash/read commands, you get **20–40 controller LLM intervention decisions** per verification — slow and expensive.

### Option A — Deterministic auto-approve in harness (good middle ground)

In `controller/policies.py` `decide_intervention()`, before calling the LLM:

- Auto-approve: `Read`, `Glob`, `Grep`, read-only `Bash` (`ls`, `cat`, `pytest`, `curl`, etc.)
- Auto-deny: `Write`, `Edit`, project file creation (verification agent shouldn’t need these anyway)
- LLM only for ambiguous `Bash`

Verification agent already blocks write tools via `disallowedTools` in `verificationAgent.ts`.

### Option B — Tiered `canUseTool` in gRPC server (best performance)

Patch `server.ts` so safe tools auto-allow without `action_required`:

```typescript
canUseTool: async (tool, input, ...) => {
  const readOnlyTools = new Set(['Read', 'Glob', 'Grep', 'WebFetch', ...])
  if (readOnlyTools.has(tool.name)) {
    call.write({ tool_start: { ... } })
    return { behavior: 'allow' }
  }
  // Agent tool spawning verification: auto-allow
  if (tool.name === 'Agent' && input?.subagent_type === 'verification') {
    return { behavior: 'allow' }
  }
  // ... existing action_required for Bash/Write/Edit
}
```

You can still route risky bash through the harness controller.

### Option C — Keep LLM for every intervention

Works but expect validation-style runs to hit `max_decisions` quickly unless limits are raised.

---

## Step 4 — Timeout implications

A verification subagent runs **inside one harness backend turn**. Many commands in one turn can hit:

- Idle timeout / `HARNESS_TURN_TIMEOUT` (default 300s; idle-based — max gap without a gRPC event)

If verification subagents time out often, either:

- Raise `HARNESS_TURN_TIMEOUT` for generation turns, or
- Keep **separate validation sessions** (current design) for long verify passes

---

## Integration patterns (how much to offload)

### Pattern 1 — “Verifier inside generation” (moderate offload)

```
Generation turn(s):
  main agent implements → spawns verification → fixes → re-spawns until PASS
Harness validation phase:
  lightweight spot-check OR --skip-verification
```

**Pros:** Reuses Chakra’s battle-tested verifier prompt.  
**Cons:** No `validation_plan.json`, no structured step loop; harder to debug; same-turn timeout risk.

### Pattern 2 — “Explore/plan during generation only” (quality boost, keep harness validation)

```
Generation: plan → general-purpose implement
Validation: keep existing verification/ controller (unchanged)
```

**Pros:** Better upfront design; keeps structured validation artifacts.  
**Cons:** More subagent calls during generation.

### Pattern 3 — “Replace harness validation with in-backend verifier” (aggressive offload)

```
Generation must end with VERDICT: PASS from verification subagent
Skip or drastically shorten verification/ phase
Repair: tell main agent to fix + re-verify
```

**Pros:** Less duplicate work.  
**Cons:** Loses `VALIDATION_PLAN_UPDATE` protocol, evidence files, planning state machine — the exact pieces you’re fixing in the validation deadlock. **Not recommended** until in-backend verification is proven stable.

### Recommended hybrid (practical)

| Phase | Who verifies |
|-------|----------------|
| Generation | Backend spawns `verification` before claiming done (Chakra behavior) |
| Harness validation | Shorter “audit” pass: confirm `VERDICT`, re-run 2–3 commands, check repo scope |
| Repair | Unchanged isolated repair sessions |

This offloads **heavy adversarial probing** to Chakra while keeping **orchestration, artifacts, and fail-fast policy** in the harness.

---

## Agent-by-agent usage guide

### `verification`

**When:** After non-trivial implementation (3+ file edits, APIs, infra).  
**How (backend message):**

```text
Spawn Agent with subagent_type="verification" and prompt containing:
- Original user objective
- List of files changed
- Brief approach summary
- Absolute path: experiments/<workdir>/
```

**Harness parses:** `VERDICT: PASS|FAIL|PARTIAL` from tool result / final text (regex, same as Chakra CLI).

**Cannot replace entirely:** Your validation phase’s `VALIDATION_PLAN_UPDATE` JSON, plan steps, and `validation_plan.json` — unless you drop that protocol.

### `general-purpose`

**When:** Large implementation delegated from main thread.  
**Risk:** Subagent can write files; every write needs intervention approval.  
**Use if:** Generation turns are getting too shallow because main agent does repo setup only.

### `Explore`

**When:** Backend needs broad codebase search before editing.  
**Safe:** Read-only; good candidate for auto-approve interventions.

### `plan`

**When:** Complex projects (snake + AI + A* + difficulty levels).  
**Output:** Prose plan in conversation — you could save it to `logs/` from harness if desired.  
**Pair with:** `general-purpose` for execution.

---

## What you should NOT expect

Even with all agents enabled:

| Still need harness for | Why |
|------------------------|-----|
| Orchestrator gen → val → repair | Chakra has no pipeline state machine |
| Controller LLM (or auto-approve policy) | gRPC always calls `canUseTool` client |
| `validation_plan.json` / plan sync | Chakra verifier uses prose + `VERDICT:` only |
| Completion guards | Chakra uses soft TodoWrite nudges |
| GUI launch blocking | Your `intervention_guard.py` |
| Experiment logs / exit codes | Harness `main.py` |

---

## Suggested rollout order

1. **Patch `grpc/server.ts`** — register `VERIFICATION_AGENT` (+ optionally `EXPLORE`, `PLAN`, `GENERAL_PURPOSE`).
2. **Restart Chakra** — `./scripts/start_chakra.sh`.
3. **Smoke test** — send a manual gRPC message: “Spawn Agent subagent_type=verification to run `python -m py_compile main.py` on this repo.” Confirm `Agent` tool works.
4. **Harness: deterministic intervention auto-approve** for read-only tools (or tiered `canUseTool`).
5. **Harness: generation bootstrap + completion guard** — require verification subagent / `VERDICT: PASS`.
6. **Run snake game experiment** — compare quality vs validation-only offload.
7. **Only then** consider shortening the separate validation phase.

---

## README constraint note

Your README says `harness/chakra` is read-only. Enabling agents **requires editing `grpc/server.ts`** (and possibly `builtInAgents.ts`). Treat that as an intentional local fork exception, document it, and restart Chakra after changes.

---

## Quick reference: files to touch

| File | Change |
|------|--------|
| `harness/chakra/src/grpc/server.ts` | `agents: [...]` instead of `[]`; optional tiered `canUseTool` |
| `controller/policies.py` / `completion_guard.py` | Bootstrap + completion rules for verification |
| `controller/policies.py` | Auto-approve safe interventions |
| `controller/prompt_builder.py` | Document subagent strategy for controller LLM |
| `verification/` (optional) | Slim to spot-check if in-backend verifier is trusted |
| `.env` | `HARNESS_TURN_TIMEOUT`, `HARNESS_CONTROLLER_LLM_TIMEOUT`, `CLAUDE_STREAM_IDLE_TIMEOUT_MS` if runs are long |

---










my_idea:

1. The repo generation is going to be larger ones as well so I want it to work accordingly and use plan agent almost always because small or medium repos also need planning. 
2. the completion guard should include that only end if max turn count reached or (verification agent was spawned and verdict pass ) - these two must happen verification agent must be involved and then if verdict is true only then complete. 
3. handle intervention: Option A — Deterministic auto-approve in harness
4. more subagents call should not be a problem is what i think be it during generation or validation or repair. So, the integratio pattern that I want is something like this: During generation first a plan agent should be called. It should plan everything based on the input prompt instructions and then. save the plan in the project directory in plan.md file which can be updated later if needed. then another agent which works best for generation should start with the implementation task. All these agents should be of inside of chakra nothing to implement in interface side. And once the initial generation task is done and the generation agent gives finished then a loop should begin. This loop only manages the invocation of the chakra subagents and checks when the agents return validation pass. This loop should be on the interface side where first we invoke the verifier subagent of chakra to verify the generated repo. Then it should return the complete report with all of the errors and the location where it was found. Then the loop should again call for two agents, first plan subagent to assess the problems reported and then based on that create a plan to repair. Then the repair subagent repairs everything. Once repairing is done and repair agent gives repairing done, then the loop starts again and the verifier agent is called again to verify that everything is working and is implemented as per plan and the project is buillt properly or is getting complied without errors of any kind. This should be an extreme check as I don't want any surprises. Then if the verification stage is passes only then the loop end otherwise it keeps on working until the project is complete and ready to use on production quality. Everything in the project should be picture perfect. No validation or repair nothing should happen on interface side just check to continue or not and log. I don't need to have all of the validation plan update and everything. Not necessary. But I want the chakra subagents to be working on everything properly. 
Also, using the explore subagent whereever necessary to safely read the files at any stage of the project generation. The logging should be done naturally and don't for anything to be done by the backend. 





phasewise plan:

Your overall direction is sound, but I would make one architectural change.

I would not expose “generation agent”, “repair agent”, etc. as separate harness concepts. Chakra already has subagents that are specialized for these workloads. The harness should become an orchestrator, not another implementation layer.

The harness should only decide:

* which Chakra subagent to invoke,
* when to invoke it,
* when to terminate,
* what to log.

Everything else should happen inside Chakra.

That keeps responsibilities clean and allows you to benefit from future Chakra improvements without rewriting harness logic.

Below is the implementation plan I would give Cursor.

⸻

Chakra Subagent Integration & Autonomous Generation Pipeline

Objective

Refactor the headless harness so that repository planning, implementation, verification, exploration, and repair are delegated to Chakra’s built-in subagents rather than being implemented by the harness itself.

The harness should become a lightweight orchestration layer responsible only for:

* starting workflows,
* invoking appropriate Chakra subagents,
* maintaining orchestration state,
* logging every stage,
* deciding whether another iteration is required.

The harness must never duplicate verification or repair logic that already exists inside Chakra.

⸻

High-Level Architecture

The overall workflow should become:

Generation Request
        │
        ▼
Plan Agent
        │
        ▼
Save plan.md
        │
        ▼
Implementation Agent
        │
        ▼
Verification Loop
        │
        ▼
Verification Agent
        │
        ├─────────────── PASS ───────────────► Finish
        │
        ▼
FAIL
        │
        ▼
Planning Agent
(Create repair strategy)
        │
        ▼
Repair Agent
        │
        ▼
Verification Agent
        │
        ▼
Repeat until PASS or iteration limit

The interface should never perform validation itself.

It should only orchestrate Chakra.

⸻

Phase 1 — Enable Chakra Built-in Subagents

Objective

Enable Chakra’s built-in agents for every gRPC session.

Currently:

agents: []

should be replaced with the built-in agent registry.

Register:

* plan
* verification
* Explore
* general-purpose

using explicit imports rather than feature-gated discovery.

The harness should always have access to these agents regardless of feature flags.

⸻

Phase 2 — Generation Workflow

Generation should no longer begin with implementation.

Instead, every generation session must begin with planning.

Step 1

Always invoke the plan subagent.

Planning should not be optional.

Even small repositories should receive an implementation plan.

The planning prompt should include:

* original objective
* repository location
* expected deliverables
* technology stack (if known)

The generated plan must be written to

plan.md

inside the repository.

This becomes the authoritative implementation roadmap.

⸻

Step 2

Invoke the most appropriate implementation agent.

Normally this should be

general-purpose

unless another specialized agent is clearly more appropriate.

The implementation agent should receive:

* original objective
* plan.md
* repository root

The implementation agent should complete the initial repository.

⸻

Step 3

Implementation finishes only when the implementation agent explicitly reports completion.

At this point generation transitions into verification orchestration.

⸻

Phase 3 — Completion Guard

The completion guard must become much stricter.

Generation may terminate only when one of the following conditions is true.

Condition 1

Maximum controller turn count has been reached.

or

Condition 2

ALL of the following are true:

* verification subagent was invoked
* verification returned

VERDICT: PASS

* verification completed successfully

Generation must never terminate before verification has been executed.

Self-reported completion by the implementation agent is insufficient.

The verification agent becomes the authoritative source of completion.

⸻

Phase 4 — Verification & Repair Orchestration

The harness should not contain validation logic.

Instead it should orchestrate Chakra verification agents.

The workflow becomes:

Verification Agent
        │
        ▼
VERDICT?

⸻

PASS

Immediately terminate generation.

Persist all logs.

Save verifier report.

Finish.

⸻

FAIL

Receive the complete verification report.

Store it.

Then begin repair.

⸻

Phase 5 — Repair Workflow

Repair begins only after a failed verification.

Repair should consist of two Chakra subagents.

Step 1

Invoke the plan agent.

The planning agent receives:

* verifier report
* current repository
* existing plan.md

Its job is to:

* analyse failures
* determine root causes
* update plan.md
* produce a repair strategy

⸻

Step 2

Invoke the repair implementation agent.

Normally this will again be

general-purpose

unless another implementation agent is more suitable.

The repair agent receives:

* verifier report
* updated plan.md
* repository

Its responsibility is to repair every reported issue.

No verification should occur during repair.

⸻

Step 3

When repair completes:

restart verification.

Verification
      │
      ▼
PASS ?

If PASS:

stop.

Otherwise:

repeat.

⸻

Phase 6 — Verification Loop

The interface owns only the orchestration loop.

The backend owns all engineering work.

The interface repeatedly performs:

Verification
↓
PASS ?
↓
Repair Planning
↓
Repair
↓
Verification

until

VERDICT: PASS

or

maximum repair iterations.

No validation logic should exist in Python.

No repair logic should exist in Python.

Python only decides which subagent to invoke next.

⸻

Phase 7 — Explore Agent Integration

The Explore subagent should be available throughout the workflow.

Whenever a planning, implementation, verification, or repair task requires broad repository inspection, the backend should use the Explore agent rather than repeatedly reading files manually.

The harness should expose the Explore agent but should never force its use.

The backend should decide when repository-wide exploration is beneficial.

⸻

Phase 8 — Deterministic Intervention Policy

Replace controller-based intervention reasoning with deterministic approval.

Implement Option A.

Automatically approve safe tools including:

* Read
* Glob
* Grep
* LS
* Find
* Tree
* Cat
* File searches
* Verification commands
* Build commands
* Test commands
* Compilation commands
* Runtime execution commands
* Verification agent invocation
* Plan agent invocation
* Explore agent invocation

Automatically deny operations outside the repository boundary.

Only ambiguous or potentially unsafe operations should require controller reasoning.

This significantly reduces controller latency while preserving safety.

⸻

Phase 9 — Logging

The harness should log orchestration events only.

The backend remains responsible for engineering work.

Each iteration should produce structured logs containing:

Iteration Number
Current Stage
Agent Invoked
Agent Type
Reason For Invocation
Start Time
End Time
Duration
Verification Verdict
Repair Summary
Plan Updates
Files Modified
Termination Reason

Persist:

plan.md

and every updated revision.

Retain all verification reports for every iteration.

Retain all repair summaries.

Do not require the backend to produce special logging formats.

The harness should collect and organize information naturally from backend responses.

⸻

Phase 10 — Final Design Principles

The final architecture should follow these principles:

* The harness is an orchestration layer, not an engineering layer.
* Chakra subagents own planning, implementation, exploration, verification, and repair.
* Every repository begins with planning.
* plan.md is the canonical implementation plan and evolves throughout the lifecycle.
* Verification is the only authority that may declare a repository complete.
* Failed verification always results in a planning phase before repair.
* Repair never validates its own work.
* Validation and repair are completely separated.
* The interface only decides which Chakra subagent runs next and records the workflow.
* No validation heuristics, validation plans, repair strategies, or engineering logic should exist in the harness.
* The system should iterate autonomously until the repository reaches production-quality completion or a configured iteration limit is reached.

