# Category batch: cms_content (all 10) — paste into Chakra

You are running a **datagen category marathon** for harness evaluation.
Category focus: **CMS/content — editable content flows in browser**.

## Non-negotiable rules

1. Complete the **10 tasks below in order** (01 → 10). Do not skip.
2. Each task is a **separate app/project** under its own folder `task_cms_content_NN/` (use the workdir listed).
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

Tag every DONE note with category `cms_content` so logs are easy to grep.

---

## Task 01 — Digital library management system
**workdir:** `task_cms_content_01`
**id:** `cms_content_01_digital-library-management-system`
**source:** `archive:5`
**dimensions:** complexity=low, value=medium, language_runtime=python, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=multi_turn_repair, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Create a complete library management system using Django. The application should support librarian and student accounts, book catalog management, borrowing and returning books, overdue tracking, reservation queues, notifications, search with multiple filters, and borrowing history. Include authentication, role-based permissions, SQLite database support, and automated unit tests covering the core workflows.

### Done criteria for this task
- App lives under `task_cms_content_01/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=browser_smoke, tools=mixed)

When done, print `DONE task_1: Digital library management system` and start the next task immediately.

---

## Task 02 — Notes and knowledge base
**workdir:** `task_cms_content_02`
**id:** `cms_content_02_notes-and-knowledge-base`
**source:** `archive:python_8`
**dimensions:** complexity=hard, value=hard, language_runtime=typescript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=visual_diff, session_shape=approval_gated, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a Notes & Knowledge Base app in Python with nested pages, tags, full-text search, and markdown rendering.

### Done criteria for this task
- App lives under `task_cms_content_02/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=visual_diff, tools=edit_heavy)

When done, print `DONE task_2: Notes and knowledge base` and start the next task immediately.

---

## Task 03 — University course registration portal
**workdir:** `task_cms_content_03`
**id:** `cms_content_03_university-course-registration-portal`
**source:** `archive:python_11`
**dimensions:** complexity=medium, value=low, language_runtime=javascript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=single_shot, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Build a University Course Registration Portal: course catalog, student enrollment, waitlists, conflicts detection, and admin overrides.

### Done criteria for this task
- App lives under `task_cms_content_03/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_3: University course registration portal` and start the next task immediately.

---

## Task 04 — Magazine CMS with issues
**workdir:** `task_cms_content_04`
**id:** `cms_content_04_magazine-cms-with-issues`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=csharp, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=multi_turn_repair, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=empty_scratch

### User request

Create a magazine CMS: issues, articles, authors, draft/publish workflow, and public reading site.

### Done criteria for this task
- App lives under `task_cms_content_04/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_4: Magazine CMS with issues` and start the next task immediately.

---

## Task 05 — Podcast episode CMS
**workdir:** `task_cms_content_05`
**id:** `cms_content_05_podcast-episode-cms`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=cpp, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=resume_mid_task, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Build a podcast CMS for episodes, show notes, RSS feed generation, and guest profiles.

### Done criteria for this task
- App lives under `task_cms_content_05/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=browser_smoke, tools=mixed)

When done, print `DONE task_5: Podcast episode CMS` and start the next task immediately.

---

## Task 06 — Internal wiki with approvals
**workdir:** `task_cms_content_06`
**id:** `cms_content_06_internal-wiki-with-approvals`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=rust, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=multi_turn_repair, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create an internal company wiki with page hierarchy, edit approvals, and change history diffs.

### Done criteria for this task
- App lives under `task_cms_content_06/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_6: Internal wiki with approvals` and start the next task immediately.

---

## Task 07 — Event listing & RSVP site
**workdir:** `task_cms_content_07`
**id:** `cms_content_07_event-listing-rsvp-site`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=go, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=approval_gated, tool_profile=mixed, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Build an event listing CMS with RSVPs, capacity limits, calendar view, and organizer dashboards.

### Done criteria for this task
- App lives under `task_cms_content_07/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=mixed)

When done, print `DONE task_7: Event listing & RSVP site` and start the next task immediately.

---

## Task 08 — Recipe publisher
**workdir:** `task_cms_content_08`
**id:** `cms_content_08_recipe-publisher`
**source:** `original`
**dimensions:** complexity=low, value=low, language_runtime=java, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=single_shot, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a recipe publisher CMS: ingredients, steps, tags, nutrition fields, and public browse/search.

### Done criteria for this task
- App lives under `task_cms_content_08/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_8: Recipe publisher` and start the next task immediately.

---

## Task 09 — Newsroom editorial desk
**workdir:** `task_cms_content_09`
**id:** `cms_content_09_newsroom-editorial-desk`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=typescript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=multi_turn_repair, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=empty_scratch

### User request

Build a newsroom desk: story assignments, statuses (pitch→edit→publish), embargo times, and role-based access.

### Done criteria for this task
- App lives under `task_cms_content_09/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_9: Newsroom editorial desk` and start the next task immediately.

---

## Task 10 — Documentation portal versioned
**workdir:** `task_cms_content_10`
**id:** `cms_content_10_documentation-portal-versioned`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=python, artifact_type=web_fullstack, task_family=documentation, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=resume_mid_task, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=partial_scaffold

### User request

Create a versioned docs portal (v1/v2), markdown pages, sidebar nav, and search across versions.

### Done criteria for this task
- App lives under `task_cms_content_10/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_10: Documentation portal versioned` and start the next task immediately.

---

## After all 10 (cms_content)

Print a final summary table: task id | path | stack | complexity | how to run.
Then stop.
