# Category batch: monitoring_ops (all 10) — paste into Chakra

You are running a **datagen category marathon** for harness evaluation.
Category focus: **monitoring/ops — metrics dashboards or alert demos**.

## Non-negotiable rules

1. Complete the **10 tasks below in order** (01 → 10). Do not skip.
2. Each task is a **separate app/project** under its own folder `task_monitoring_ops_NN/` (use the workdir listed).
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

Tag every DONE note with category `monitoring_ops` so logs are easy to grep.

---

## Task 01 — Network monitoring dashboard
**workdir:** `task_monitoring_ops_01`
**id:** `monitoring_ops_01_network-monitoring-dashboard`
**source:** `archive:8`
**dimensions:** complexity=medium, value=medium, language_runtime=python, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=multi_turn_repair, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=empty_scratch

### User request

Create a network monitoring application using Python and FastAPI. The backend should periodically ping configurable hosts, measure response times, detect outages, and expose REST APIs for historical metrics. Build a React dashboard that visualizes uptime percentages, latency graphs, downtime history, and device health using interactive charts. Support configurable monitoring intervals and persistent storage using SQLite.

### Done criteria for this task
- App lives under `task_monitoring_ops_01/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_1: Network monitoring dashboard` and start the next task immediately.

---

## Task 02 — Service health board
**workdir:** `task_monitoring_ops_02`
**id:** `monitoring_ops_02_service-health-board`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=typescript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=resume_mid_task, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=partial_scaffold

### User request

Build a service health board aggregating synthetic checks, dependency status, and a public status page with incident history.

### Done criteria for this task
- App lives under `task_monitoring_ops_02/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_2: Service health board` and start the next task immediately.

---

## Task 03 — Log error rate monitor
**workdir:** `task_monitoring_ops_03`
**id:** `monitoring_ops_03_log-error-rate-monitor`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=javascript, artifact_type=cli_tool, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=multi_turn_repair, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Create a log tail monitor that counts error patterns, charts rates, and fires threshold alerts.

### Done criteria for this task
- App lives under `task_monitoring_ops_03/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=browser_smoke, tools=mixed)

When done, print `DONE task_3: Log error rate monitor` and start the next task immediately.

---

## Task 04 — Cron job watchdog
**workdir:** `task_monitoring_ops_04`
**id:** `monitoring_ops_04_cron-job-watchdog`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=csharp, artifact_type=backend_api, task_family=coding_implement, agent_topology=single_agent, verification_mode=visual_diff, session_shape=approval_gated, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Build a cron/job watchdog: expected run windows, last-success heartbeats, and missed-run alerts.

### Done criteria for this task
- App lives under `task_monitoring_ops_04/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=visual_diff, tools=edit_heavy)

When done, print `DONE task_4: Cron job watchdog` and start the next task immediately.

---

## Task 05 — Disk and memory host agent
**workdir:** `task_monitoring_ops_05`
**id:** `monitoring_ops_05_disk-and-memory-host-agent`
**source:** `original`
**dimensions:** complexity=medium, value=low, language_runtime=cpp, artifact_type=cli_tool, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=single_shot, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Implement a local host agent that samples CPU/mem/disk and pushes metrics to a small collector UI.

### Done criteria for this task
- App lives under `task_monitoring_ops_05/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_5: Disk and memory host agent` and start the next task immediately.

---

## Task 06 — SSL/HTTP probe farm
**workdir:** `task_monitoring_ops_06`
**id:** `monitoring_ops_06_ssl-http-probe-farm`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=rust, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=multi_turn_repair, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=empty_scratch

### User request

Create an HTTP probe farm: configured URLs, expected status codes, latency SLOs, and failure screenshots stubs.

### Done criteria for this task
- App lives under `task_monitoring_ops_06/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_6: SSL/HTTP probe farm` and start the next task immediately.

---

## Task 07 — On-call rotation calendar
**workdir:** `task_monitoring_ops_07`
**id:** `monitoring_ops_07_on-call-rotation-calendar`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=go, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=resume_mid_task, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Build an on-call rotation calendar with schedules, overrides, and alert routing contact list (no real PagerDuty).

### Done criteria for this task
- App lives under `task_monitoring_ops_07/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=browser_smoke, tools=mixed)

When done, print `DONE task_7: On-call rotation calendar` and start the next task immediately.

---

## Task 08 — Queue depth observatory
**workdir:** `task_monitoring_ops_08`
**id:** `monitoring_ops_08_queue-depth-observatory`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=java, artifact_type=web_fullstack, task_family=data_visualization, agent_topology=single_agent, verification_mode=static_pass, session_shape=multi_turn_repair, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a queue-depth observatory for fake workers: publish lag metrics, backlog charts, and saturation warnings.

### Done criteria for this task
- App lives under `task_monitoring_ops_08/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_8: Queue depth observatory` and start the next task immediately.

---

## Task 09 — Uptime Excel weekly report
**workdir:** `task_monitoring_ops_09`
**id:** `monitoring_ops_09_uptime-excel-weekly-report`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=typescript, artifact_type=spreadsheet_workbook, task_family=spreadsheet_excel, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=approval_gated, tool_profile=mixed, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Build a tool that reads uptime check CSVs and produces a weekly Excel report with SLO burn and incident list.

### Done criteria for this task
- App lives under `task_monitoring_ops_09/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=mixed)

When done, print `DONE task_9: Uptime Excel weekly report` and start the next task immediately.

---

## Task 10 — Synthetic transaction checker
**workdir:** `task_monitoring_ops_10`
**id:** `monitoring_ops_10_synthetic-transaction-checker`
**source:** `original`
**dimensions:** complexity=low, value=low, language_runtime=python, artifact_type=cli_tool, task_family=testing_qa, agent_topology=single_agent, verification_mode=static_pass, session_shape=single_shot, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Implement a synthetic login→search→checkout transaction checker with step timings and pass/fail reports.

### Done criteria for this task
- App lives under `task_monitoring_ops_10/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_10: Synthetic transaction checker` and start the next task immediately.

---

## After all 10 (monitoring_ops)

Print a final summary table: task id | path | stack | complexity | how to run.
Then stop.
