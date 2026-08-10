# Category batch: collaborative_realtime (all 10) — paste into Chakra

You are running a **datagen category marathon** for harness evaluation.
Category focus: **realtime collab — multi-user or live-updating UI**.

## Non-negotiable rules

1. Complete the **10 tasks below in order** (01 → 10). Do not skip.
2. Each task is a **separate app/project** under its own folder `task_collaborative_realtime_NN/` (use the workdir listed).
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

Tag every DONE note with category `collaborative_realtime` so logs are easy to grep.

---

## Task 01 — Slack-style team chat
**workdir:** `task_collaborative_realtime_01`
**id:** `collaborative_realtime_01_slack-style-team-chat`
**source:** `archive:bonus`
**dimensions:** complexity=medium, value=low, language_runtime=python, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=single_shot, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Build a Slack-style team chat application with channels, private messaging, notifications, and file sharing.

### Done criteria for this task
- App lives under `task_collaborative_realtime_01/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_1: Slack-style team chat` and start the next task immediately.

---

## Task 02 — Multiplayer kanban board live sync
**workdir:** `task_collaborative_realtime_02`
**id:** `collaborative_realtime_02_multiplayer-kanban-board-live-sync`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=typescript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=multi_turn_repair, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=empty_scratch

### User request

Create a multiplayer kanban board where cards and columns sync in real time across users with presence indicators, conflict-safe moves, and room-based boards.

### Done criteria for this task
- App lives under `task_collaborative_realtime_02/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_2: Multiplayer kanban board live sync` and start the next task immediately.

---

## Task 03 — Pair programming shared editor
**workdir:** `task_collaborative_realtime_03`
**id:** `collaborative_realtime_03_pair-programming-shared-editor`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=javascript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=resume_mid_task, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Build a pair-programming web app with a shared code editor, cursors for each user, chat sidebar, and session links. Use WebSockets for sync.

### Done criteria for this task
- App lives under `task_collaborative_realtime_03/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=browser_smoke, tools=mixed)

When done, print `DONE task_3: Pair programming shared editor` and start the next task immediately.

---

## Task 04 — Live auction room
**workdir:** `task_collaborative_realtime_04`
**id:** `collaborative_realtime_04_live-auction-room`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=csharp, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=multi_turn_repair, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a real-time auction room platform: users join rooms, place bids, see live bid feed and countdown timers, and get notified when outbid.

### Done criteria for this task
- App lives under `task_collaborative_realtime_04/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_4: Live auction room` and start the next task immediately.

---

## Task 05 — Classroom quiz live leaderboard
**workdir:** `task_collaborative_realtime_05`
**id:** `collaborative_realtime_05_classroom-quiz-live-leaderboard`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=cpp, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=approval_gated, tool_profile=mixed, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Build a live classroom quiz app where a teacher pushes questions and students answer in real time with a running leaderboard.

### Done criteria for this task
- App lives under `task_collaborative_realtime_05/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=mixed)

When done, print `DONE task_5: Classroom quiz live leaderboard` and start the next task immediately.

---

## Task 06 — Collaborative markdown notes
**workdir:** `task_collaborative_realtime_06`
**id:** `collaborative_realtime_06_collaborative-markdown-notes`
**source:** `original`
**dimensions:** complexity=low, value=low, language_runtime=rust, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=single_shot, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a collaborative markdown notes app with rooms, live caret presence, version history snapshots, and export to Markdown/HTML.

### Done criteria for this task
- App lives under `task_collaborative_realtime_06/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_6: Collaborative markdown notes` and start the next task immediately.

---

## Task 07 — Ops war-room incident chat
**workdir:** `task_collaborative_realtime_07`
**id:** `collaborative_realtime_07_ops-war-room-incident-chat`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=go, artifact_type=backend_api, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=multi_turn_repair, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=empty_scratch

### User request

Build an incident war-room chat with channels per incident, @mentions, severity tags, and a timeline of status updates synced live.

### Done criteria for this task
- App lives under `task_collaborative_realtime_07/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_7: Ops war-room incident chat` and start the next task immediately.

---

## Task 08 — Shared music listening room
**workdir:** `task_collaborative_realtime_08`
**id:** `collaborative_realtime_08_shared-music-listening-room`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=java, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=resume_mid_task, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=partial_scaffold

### User request

Create a synchronized listening room: queue tracks, play/pause sync across clients, chat, and host controls.

### Done criteria for this task
- App lives under `task_collaborative_realtime_08/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_8: Shared music listening room` and start the next task immediately.

---

## Task 09 — Live CSV co-editing sheet
**workdir:** `task_collaborative_realtime_09`
**id:** `collaborative_realtime_09_live-csv-co-editing-sheet`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=typescript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=multi_turn_repair, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Build a lightweight collaborative spreadsheet for CSV data with cell editing, live sync, and conflict highlighting (not Excel-plugin).

### Done criteria for this task
- App lives under `task_collaborative_realtime_09/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=browser_smoke, tools=mixed)

When done, print `DONE task_9: Live CSV co-editing sheet` and start the next task immediately.

---

## Task 10 — Remote design critique board
**workdir:** `task_collaborative_realtime_10`
**id:** `collaborative_realtime_10_remote-design-critique-board`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=python, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=visual_diff, session_shape=approval_gated, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a real-time design critique board: upload images, pin comments with coordinates, resolve threads, and show live viewers.

### Done criteria for this task
- App lives under `task_collaborative_realtime_10/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=visual_diff, tools=edit_heavy)

When done, print `DONE task_10: Remote design critique board` and start the next task immediately.

---

## After all 10 (collaborative_realtime)

Print a final summary table: task id | path | stack | complexity | how to run.
Then stop.
