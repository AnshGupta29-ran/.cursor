# Category batch: distributed_systems (all 10) — paste into Chakra

You are running a **datagen category marathon** for harness evaluation.
Category focus: **distributed systems — multi-process/service demo**.

## Non-negotiable rules

1. Complete the **10 tasks below in order** (01 → 10). Do not skip.
2. Each task is a **separate app/project** under its own folder `task_distributed_systems_NN/` (use the workdir listed).
3. For each task: implement until **demoable** (browser open, CLI works, or game playable). Install deps, start servers, fix bugs.
4. **Do not ask for approval** between tasks — continue automatically.
5. After each task: short note `DONE task_N: <title> — path + how to run`.
6. **Vary implementation** across tasks — different stacks/patterns matching the dimension targets. Do not clone the same scaffold 10 times.
7. Challenge the harness: use tools, tests, browser checks, repairs when dims say so.
8. Prefer completing a solid MVP over endless polish; then move to the next task.

## Stats / ledger

Keep the stats site running once (`python -m prompt_stats serve`).
Open http://127.0.0.1:8787/ — hard-refresh the page to pull latest Chakra
sessions into the dashboard (no separate `collect` command).

Tag every DONE note with category `distributed_systems` so logs are easy to grep.

---

## Task 01 — Distributed task queue (Go)
**workdir:** `task_distributed_systems_01`
**id:** `distributed_systems_01_distributed-task-queue-go`
**source:** `archive:10`
**dimensions:** complexity=hard, value=hard, language_runtime=go, artifact_type=backend_api, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=approval_gated, tool_profile=mixed, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Create a distributed task queue framework using Go. Implement a central scheduler, multiple worker nodes, task prioritization, retries with exponential backoff, worker heartbeats, failure detection, persistent job storage using SQLite, and a REST API for submitting and monitoring jobs. Include structured logging, graceful shutdown, concurrency using goroutines, and automated integration tests demonstrating multiple workers processing jobs simultaneously.

### Done criteria for this task
- App lives under `task_distributed_systems_01/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=mixed)

When done, print `DONE task_1: Distributed task queue (Go)` and start the next task immediately.

---

## Task 02 — Priority job scheduler
**workdir:** `task_distributed_systems_02`
**id:** `distributed_systems_02_priority-job-scheduler`
**source:** `original`
**dimensions:** complexity=low, value=low, language_runtime=rust, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=single_shot, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Build a priority job scheduler with delayed jobs, dead-letter queue, and an admin UI for retry/cancel.

### Done criteria for this task
- App lives under `task_distributed_systems_02/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_2: Priority job scheduler` and start the next task immediately.

---

## Task 03 — Leader election toy cluster
**workdir:** `task_distributed_systems_03`
**id:** `distributed_systems_03_leader-election-toy-cluster`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=python, artifact_type=cli_tool, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=multi_turn_repair, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=empty_scratch

### User request

Implement a toy leader-election cluster (raft-lite or bully): nodes, heartbeat, failover demo CLI.

### Done criteria for this task
- App lives under `task_distributed_systems_03/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_3: Leader election toy cluster` and start the next task immediately.

---

## Task 04 — Pub/sub message broker lite
**workdir:** `task_distributed_systems_04`
**id:** `distributed_systems_04_pub-sub-message-broker-lite`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=java, artifact_type=library_sdk, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=resume_mid_task, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=partial_scaffold

### User request

Create an in-process pub/sub broker with topics, durable subscribers stub, and backpressure stats.

### Done criteria for this task
- App lives under `task_distributed_systems_04/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_4: Pub/sub message broker lite` and start the next task immediately.

---

## Task 05 — MapReduce wordcount lab
**workdir:** `task_distributed_systems_05`
**id:** `distributed_systems_05_mapreduce-wordcount-lab`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=csharp, artifact_type=cli_tool, task_family=data_wrangling, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=multi_turn_repair, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Build a mini MapReduce wordcount: split files, map workers, shuffle, reduce, and merge output.

### Done criteria for this task
- App lives under `task_distributed_systems_05/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=browser_smoke, tools=mixed)

When done, print `DONE task_5: MapReduce wordcount lab` and start the next task immediately.

---

## Task 06 — Distributed lock service
**workdir:** `task_distributed_systems_06`
**id:** `distributed_systems_06_distributed-lock-service`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=go, artifact_type=backend_api, task_family=coding_implement, agent_topology=single_agent, verification_mode=visual_diff, session_shape=approval_gated, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Implement a distributed lock service API with TTL, fencing tokens, and contention tests.

### Done criteria for this task
- App lives under `task_distributed_systems_06/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=visual_diff, tools=edit_heavy)

When done, print `DONE task_6: Distributed lock service` and start the next task immediately.

---

## Task 07 — Sharded key-value store
**workdir:** `task_distributed_systems_07`
**id:** `distributed_systems_07_sharded-key-value-store`
**source:** `original`
**dimensions:** complexity=medium, value=low, language_runtime=typescript, artifact_type=backend_api, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=single_shot, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Create a sharded key-value store demo with consistent hashing, get/put, and rebalance command.

### Done criteria for this task
- App lives under `task_distributed_systems_07/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_7: Sharded key-value store` and start the next task immediately.

---

## Task 08 — Workflow saga orchestrator
**workdir:** `task_distributed_systems_08`
**id:** `distributed_systems_08_workflow-saga-orchestrator`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=python, artifact_type=backend_api, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=multi_turn_repair, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=empty_scratch

### User request

Build a saga/workflow orchestrator for multi-step jobs with compensations on failure.

### Done criteria for this task
- App lives under `task_distributed_systems_08/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_8: Workflow saga orchestrator` and start the next task immediately.

---

## Task 09 — Batch fan-out email workers
**workdir:** `task_distributed_systems_09`
**id:** `distributed_systems_09_batch-fan-out-email-workers`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=rust, artifact_type=backend_api, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=resume_mid_task, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Create a fan-out email sending simulator: enqueue campaigns, workers send stubs, track delivery states.

### Done criteria for this task
- App lives under `task_distributed_systems_09/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=browser_smoke, tools=mixed)

When done, print `DONE task_9: Batch fan-out email workers` and start the next task immediately.

---

## Task 10 — Clock skew demo + NTP stub
**workdir:** `task_distributed_systems_10`
**id:** `distributed_systems_10_clock-skew-demo-ntp-stub`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=javascript, artifact_type=cli_tool, task_family=analysis_reason, agent_topology=single_agent, verification_mode=static_pass, session_shape=multi_turn_repair, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Build a multi-node clock skew demo showing logical clocks/vector clocks for event ordering.

### Done criteria for this task
- App lives under `task_distributed_systems_10/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_10: Clock skew demo + NTP stub` and start the next task immediately.

---

## After all 10 (distributed_systems)

Print a final summary table: task id | path | stack | complexity | how to run.
Then stop.
