# Category batch: generic_fullstack (all 10) — paste into Chakra

You are running a **datagen category marathon** for harness evaluation.
Category focus: **generic fullstack — API + UI, browser-checkable**.

## Non-negotiable rules

1. Complete the **10 tasks below in order** (01 → 10). Do not skip.
2. Each task is a **separate app/project** under its own folder `task_generic_fullstack_NN/` (use the workdir listed).
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

Tag every DONE note with category `generic_fullstack` so logs are easy to grep.

---

## Task 01 — Hospital appointment management
**workdir:** `task_generic_fullstack_01`
**id:** `generic_fullstack_01_hospital-appointment-management`
**source:** `archive:python_3`
**dimensions:** complexity=medium, value=medium, language_runtime=python, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=resume_mid_task, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Create a Hospital Appointment Management system: doctors, patients, slots, bookings, cancellations, and reminders stub.

### Done criteria for this task
- App lives under `task_generic_fullstack_01/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=browser_smoke, tools=mixed)

When done, print `DONE task_1: Hospital appointment management` and start the next task immediately.

---

## Task 02 — URL shortener service
**workdir:** `task_generic_fullstack_02`
**id:** `generic_fullstack_02_url-shortener-service`
**source:** `archive:python_6`
**dimensions:** complexity=low, value=medium, language_runtime=typescript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=multi_turn_repair, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a URL Shortener Service with custom aliases, click analytics, and expiry.

### Done criteria for this task
- App lives under `task_generic_fullstack_02/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_2: URL shortener service` and start the next task immediately.

---

## Task 03 — Local code search engine
**workdir:** `task_generic_fullstack_03`
**id:** `generic_fullstack_03_local-code-search-engine`
**source:** `archive:python_14`
**dimensions:** complexity=hard, value=hard, language_runtime=javascript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=approval_gated, tool_profile=mixed, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Create a Local Code Search Engine that indexes a repo directory and supports fast text/symbol search with a UI.

### Done criteria for this task
- App lives under `task_generic_fullstack_03/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=mixed)

When done, print `DONE task_3: Local code search engine` and start the next task immediately.

---

## Task 04 — Community forum
**workdir:** `task_generic_fullstack_04`
**id:** `generic_fullstack_04_community-forum`
**source:** `original`
**dimensions:** complexity=low, value=low, language_runtime=csharp, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=single_shot, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Build a community forum with threads, replies, votes, moderation flags, and user profiles.

### Done criteria for this task
- App lives under `task_generic_fullstack_04/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_4: Community forum` and start the next task immediately.

---

## Task 05 — Job board
**workdir:** `task_generic_fullstack_05`
**id:** `generic_fullstack_05_job-board`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=cpp, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=multi_turn_repair, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=empty_scratch

### User request

Create a job board: employer posts, seeker applications, filters, and saved jobs.

### Done criteria for this task
- App lives under `task_generic_fullstack_05/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_5: Job board` and start the next task immediately.

---

## Task 06 — Helpdesk ticket system
**workdir:** `task_generic_fullstack_06`
**id:** `generic_fullstack_06_helpdesk-ticket-system`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=rust, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=resume_mid_task, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=partial_scaffold

### User request

Build a helpdesk ticket system with priorities, SLA timers, agent assignment, and canned responses.

### Done criteria for this task
- App lives under `task_generic_fullstack_06/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_6: Helpdesk ticket system` and start the next task immediately.

---

## Task 07 — Bookmark manager
**workdir:** `task_generic_fullstack_07`
**id:** `generic_fullstack_07_bookmark-manager`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=go, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=multi_turn_repair, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Create a bookmark manager with folders, tags, full-text search, and import/export HTML.

### Done criteria for this task
- App lives under `task_generic_fullstack_07/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=browser_smoke, tools=mixed)

When done, print `DONE task_7: Bookmark manager` and start the next task immediately.

---

## Task 08 — Survey builder
**workdir:** `task_generic_fullstack_08`
**id:** `generic_fullstack_08_survey-builder`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=java, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=visual_diff, session_shape=approval_gated, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Build a survey builder: form fields, publish link, responses table, and basic charts.

### Done criteria for this task
- App lives under `task_generic_fullstack_08/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=visual_diff, tools=edit_heavy)

When done, print `DONE task_8: Survey builder` and start the next task immediately.

---

## Task 09 — Classroom attendance app
**workdir:** `task_generic_fullstack_09`
**id:** `generic_fullstack_09_classroom-attendance-app`
**source:** `original`
**dimensions:** complexity=medium, value=low, language_runtime=typescript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=single_shot, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Create a classroom attendance app: roster, date sessions, present/absent, and export CSV.

### Done criteria for this task
- App lives under `task_generic_fullstack_09/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_9: Classroom attendance app` and start the next task immediately.

---

## Task 10 — Personal CRM lite
**workdir:** `task_generic_fullstack_10`
**id:** `generic_fullstack_10_personal-crm-lite`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=python, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=multi_turn_repair, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=empty_scratch

### User request

Build a personal CRM lite: contacts, companies, interaction notes, and follow-up reminders.

### Done criteria for this task
- App lives under `task_generic_fullstack_10/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_10: Personal CRM lite` and start the next task immediately.

---

## After all 10 (generic_fullstack)

Print a final summary table: task id | path | stack | complexity | how to run.
Then stop.
