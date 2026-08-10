# Category batch: devops_infra (all 10) — paste into Chakra

You are running a **datagen category marathon** for harness evaluation.
Category focus: **DevOps/infra — scripts, pipelines, or local stack demos**.

## Non-negotiable rules

1. Complete the **10 tasks below in order** (01 → 10). Do not skip.
2. Each task is a **separate app/project** under its own folder `task_devops_infra_NN/` (use the workdir listed).
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

Tag every DONE note with category `devops_infra` so logs are easy to grep.

---

## Task 01 — Docker container management dashboard
**workdir:** `task_devops_infra_01`
**id:** `devops_infra_01_docker-container-management-dashboard`
**source:** `archive:bonus`
**dimensions:** complexity=medium, value=medium, language_runtime=python, artifact_type=web_fullstack, task_family=devops_ops, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=resume_mid_task, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Build a Docker container management dashboard that interacts with the Docker Engine API to start, stop, inspect, and monitor containers.

### Done criteria for this task
- App lives under `task_devops_infra_01/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=browser_smoke, tools=mixed)

When done, print `DONE task_1: Docker container management dashboard` and start the next task immediately.

---

## Task 02 — Kubernetes cluster visualization
**workdir:** `task_devops_infra_02`
**id:** `devops_infra_02_kubernetes-cluster-visualization`
**source:** `archive:bonus`
**dimensions:** complexity=low, value=medium, language_runtime=go, artifact_type=web_fullstack, task_family=devops_ops, agent_topology=single_agent, verification_mode=static_pass, session_shape=multi_turn_repair, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Build a Kubernetes cluster visualization dashboard that displays nodes, pods, deployments, services, logs, and resource utilization using the Kubernetes API.

### Done criteria for this task
- App lives under `task_devops_infra_02/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_2: Kubernetes cluster visualization` and start the next task immediately.

---

## Task 03 — GitHub-like code repository platform
**workdir:** `task_devops_infra_03`
**id:** `devops_infra_03_github-like-code-repository-platform`
**source:** `archive:bonus`
**dimensions:** complexity=hard, value=hard, language_runtime=typescript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=approval_gated, tool_profile=mixed, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Build a GitHub-like code repository platform with repository browsing, issues, pull requests, authentication, and Markdown rendering.

### Done criteria for this task
- App lives under `task_devops_infra_03/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=mixed)

When done, print `DONE task_3: GitHub-like code repository platform` and start the next task immediately.

---

## Task 04 — CI pipeline status board
**workdir:** `task_devops_infra_04`
**id:** `devops_infra_04_ci-pipeline-status-board`
**source:** `original`
**dimensions:** complexity=low, value=low, language_runtime=python, artifact_type=web_fullstack, task_family=devops_ops, agent_topology=single_agent, verification_mode=static_pass, session_shape=single_shot, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a CI pipeline status board that ingests fake job events, shows stages, flaky detection, and retry buttons.

### Done criteria for this task
- App lives under `task_devops_infra_04/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_4: CI pipeline status board` and start the next task immediately.

---

## Task 05 — Terraform state explorer
**workdir:** `task_devops_infra_05`
**id:** `devops_infra_05_terraform-state-explorer`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=python, artifact_type=cli_tool, task_family=devops_ops, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=multi_turn_repair, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=empty_scratch

### User request

Build a Terraform state explorer: load state JSON, list resources, show attributes, and diff two state files.

### Done criteria for this task
- App lives under `task_devops_infra_05/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_5: Terraform state explorer` and start the next task immediately.

---

## Task 06 — Local registry + image GC
**workdir:** `task_devops_infra_06`
**id:** `devops_infra_06_local-registry-image-gc`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=rust, artifact_type=backend_api, task_family=devops_ops, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=resume_mid_task, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=partial_scaffold

### User request

Create a local container image registry stub with tag list, delete, and garbage-collection policy demo.

### Done criteria for this task
- App lives under `task_devops_infra_06/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_6: Local registry + image GC` and start the next task immediately.

---

## Task 07 — Env var & secrets sync tool
**workdir:** `task_devops_infra_07`
**id:** `devops_infra_07_env-var-secrets-sync-tool`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=javascript, artifact_type=cli_tool, task_family=devops_ops, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=multi_turn_repair, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Build an env sync tool: compare .env across environments, redact secrets in diffs, and apply patches.

### Done criteria for this task
- App lives under `task_devops_infra_07/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=browser_smoke, tools=mixed)

When done, print `DONE task_7: Env var & secrets sync tool` and start the next task immediately.

---

## Task 08 — Nginx config generator UI
**workdir:** `task_devops_infra_08`
**id:** `devops_infra_08_nginx-config-generator-ui`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=java, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=visual_diff, session_shape=approval_gated, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create an Nginx config generator UI for reverse proxy upstreams, TLS toggles, and downloadable conf.

### Done criteria for this task
- App lives under `task_devops_infra_08/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=visual_diff, tools=edit_heavy)

When done, print `DONE task_8: Nginx config generator UI` and start the next task immediately.

---

## Task 09 — Backup job orchestrator
**workdir:** `task_devops_infra_09`
**id:** `devops_infra_09_backup-job-orchestrator`
**source:** `original`
**dimensions:** complexity=medium, value=low, language_runtime=go, artifact_type=backend_api, task_family=devops_ops, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=single_shot, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Build a backup job orchestrator: schedules, destinations, retention, and restore dry-run reports.

### Done criteria for this task
- App lives under `task_devops_infra_09/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_9: Backup job orchestrator` and start the next task immediately.

---

## Task 10 — Feature flag admin console
**workdir:** `task_devops_infra_10`
**id:** `devops_infra_10_feature-flag-admin-console`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=typescript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=multi_turn_repair, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=empty_scratch

### User request

Create a feature-flag admin console with percentage rollouts, targeting rules, and audit history.

### Done criteria for this task
- App lives under `task_devops_infra_10/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_10: Feature flag admin console` and start the next task immediately.

---

## After all 10 (devops_infra)

Print a final summary table: task id | path | stack | complexity | how to run.
Then stop.
