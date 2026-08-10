# Category batch: finance_productivity (all 10) — paste into Chakra

You are running a **datagen category marathon** for harness evaluation.
Category focus: **finance/productivity — dashboards or workflow apps**.

## Non-negotiable rules

1. Complete the **10 tasks below in order** (01 → 10). Do not skip.
2. Each task is a **separate app/project** under its own folder `task_finance_productivity_NN/` (use the workdir listed).
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

Tag every DONE note with category `finance_productivity` so logs are easy to grep.

---

## Task 01 — Personal finance tracker PRD
**workdir:** `task_finance_productivity_01`
**id:** `finance_productivity_01_personal-finance-tracker-prd`
**source:** `archive:finance_prd`
**dimensions:** complexity=low, value=medium, language_runtime=python, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=multi_turn_repair, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Build a production-quality Personal Finance Tracker application from scratch. The application should allow users to manage their personal finances, track spending habits, and visualize their financial health through an intuitive interface. Support registration/auth, isolated user data, income/expense CRUD, categories, budgets, monthly/yearly summaries, dashboard charts, search/filter, and tests plus README.

### Done criteria for this task
- App lives under `task_finance_productivity_01/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=browser_smoke, tools=mixed)

When done, print `DONE task_1: Personal finance tracker PRD` and start the next task immediately.

---

## Task 02 — Personal finance manager
**workdir:** `task_finance_productivity_02`
**id:** `finance_productivity_02_personal-finance-manager`
**source:** `archive:python_1`
**dimensions:** complexity=hard, value=hard, language_runtime=typescript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=visual_diff, session_shape=approval_gated, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a Personal Finance Manager in Python with accounts, transactions, budgets, and reports runnable locally.

### Done criteria for this task
- App lives under `task_finance_productivity_02/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=visual_diff, tools=edit_heavy)

When done, print `DONE task_2: Personal finance manager` and start the next task immediately.

---

## Task 03 — Expense splitter
**workdir:** `task_finance_productivity_03`
**id:** `finance_productivity_03_expense-splitter`
**source:** `archive:python_12`
**dimensions:** complexity=medium, value=low, language_runtime=javascript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=single_shot, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Create an Expense Splitter app: groups, shared expenses, balances, and settle-up suggestions.

### Done criteria for this task
- App lives under `task_finance_productivity_03/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_3: Expense splitter` and start the next task immediately.

---

## Task 04 — Employee leave management
**workdir:** `task_finance_productivity_04`
**id:** `finance_productivity_04_employee-leave-management`
**source:** `archive:python_4`
**dimensions:** complexity=hard, value=hard, language_runtime=csharp, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=multi_turn_repair, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=empty_scratch

### User request

Create an Employee Leave Management System: leave types, balances, approvals, and calendar conflicts.

### Done criteria for this task
- App lives under `task_finance_productivity_04/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_4: Employee leave management` and start the next task immediately.

---

## Task 05 — Task and project management tool
**workdir:** `task_finance_productivity_05`
**id:** `finance_productivity_05_task-and-project-management-tool`
**source:** `archive:python_9`
**dimensions:** complexity=medium, value=medium, language_runtime=cpp, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=resume_mid_task, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Create a Task & Project Management Tool with projects, tasks, assignees, due dates, and status workflow.

### Done criteria for this task
- App lives under `task_finance_productivity_05/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=browser_smoke, tools=mixed)

When done, print `DONE task_5: Task and project management tool` and start the next task immediately.

---

## Task 06 — Invoice generator
**workdir:** `task_finance_productivity_06`
**id:** `finance_productivity_06_invoice-generator`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=rust, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=multi_turn_repair, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Build an invoice generator: clients, line items, tax, PDF/HTML export, and payment status tracking.

### Done criteria for this task
- App lives under `task_finance_productivity_06/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_6: Invoice generator` and start the next task immediately.

---

## Task 07 — Habit streak tracker API
**workdir:** `task_finance_productivity_07`
**id:** `finance_productivity_07_habit-streak-tracker-api`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=go, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=approval_gated, tool_profile=mixed, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Create a habit streak tracker API + minimal UI: daily check-ins, streaks, and weekly heatmap.

### Done criteria for this task
- App lives under `task_finance_productivity_07/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=mixed)

When done, print `DONE task_7: Habit streak tracker API` and start the next task immediately.

---

## Task 08 — Meeting notes action extractor
**workdir:** `task_finance_productivity_08`
**id:** `finance_productivity_08_meeting-notes-action-extractor`
**source:** `original`
**dimensions:** complexity=low, value=low, language_runtime=java, artifact_type=web_fullstack, task_family=analysis_reason, agent_topology=single_agent, verification_mode=static_pass, session_shape=single_shot, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Build a meeting-notes tool that stores notes and extracts action items with owners/due dates (rules or light NLP).

### Done criteria for this task
- App lives under `task_finance_productivity_08/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_8: Meeting notes action extractor` and start the next task immediately.

---

## Task 09 — Budget workbook assistant
**workdir:** `task_finance_productivity_09`
**id:** `finance_productivity_09_budget-workbook-assistant`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=typescript, artifact_type=spreadsheet_workbook, task_family=spreadsheet_excel, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=multi_turn_repair, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=empty_scratch

### User request

Create a budget workbook assistant that generates and updates an Excel monthly budget with categories and variance formulas.

### Done criteria for this task
- App lives under `task_finance_productivity_09/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_9: Budget workbook assistant` and start the next task immediately.

---

## Task 10 — OKR tracker
**workdir:** `task_finance_productivity_10`
**id:** `finance_productivity_10_okr-tracker`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=python, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=resume_mid_task, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=partial_scaffold

### User request

Build an OKR tracker: objectives, key results with progress %, check-ins, and team rollup view.

### Done criteria for this task
- App lives under `task_finance_productivity_10/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_10: OKR tracker` and start the next task immediately.

---

## After all 10 (finance_productivity)

Print a final summary table: task id | path | stack | complexity | how to run.
Then stop.
