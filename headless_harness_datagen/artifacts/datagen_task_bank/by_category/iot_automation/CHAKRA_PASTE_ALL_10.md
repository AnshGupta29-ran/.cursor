# Category batch: iot_automation (all 10) — paste into Chakra

You are running a **datagen category marathon** for harness evaluation.
Category focus: **IoT/automation — device/sim + control UI or CLI**.

## Non-negotiable rules

1. Complete the **10 tasks below in order** (01 → 10). Do not skip.
2. Each task is a **separate app/project** under its own folder `task_iot_automation_NN/` (use the workdir listed).
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

Tag every DONE note with category `iot_automation` so logs are easy to grep.

---

## Task 01 — Greenhouse sensor automation console
**workdir:** `task_iot_automation_01`
**id:** `iot_automation_01_greenhouse-sensor-automation-console`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=python, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=approval_gated, tool_profile=mixed, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Build a greenhouse IoT automation console: simulate temperature/humidity/soil sensors, set thresholds, trigger watering/fan actuators, show history charts, and schedule rules.

### Done criteria for this task
- App lives under `task_iot_automation_01/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=mixed)

When done, print `DONE task_1: Greenhouse sensor automation console` and start the next task immediately.

---

## Task 02 — Factory machine status board
**workdir:** `task_iot_automation_02`
**id:** `iot_automation_02_factory-machine-status-board`
**source:** `original`
**dimensions:** complexity=low, value=low, language_runtime=typescript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=single_shot, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a factory machine status board with simulated PLC devices, downtime reasons, OEE-style metrics, and operator acknowledgements.

### Done criteria for this task
- App lives under `task_iot_automation_02/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_2: Factory machine status board` and start the next task immediately.

---

## Task 03 — Fleet GPS tracker simulator
**workdir:** `task_iot_automation_03`
**id:** `iot_automation_03_fleet-gps-tracker-simulator`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=javascript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=multi_turn_repair, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=empty_scratch

### User request

Build a vehicle fleet tracker simulator: devices publish GPS points, map/list views, geofence alerts, and trip history.

### Done criteria for this task
- App lives under `task_iot_automation_03/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_3: Fleet GPS tracker simulator` and start the next task immediately.

---

## Task 04 — Aquarium controller dashboard
**workdir:** `task_iot_automation_04`
**id:** `iot_automation_04_aquarium-controller-dashboard`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=csharp, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=resume_mid_task, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=partial_scaffold

### User request

Create an aquarium controller dashboard: light schedules, temperature alerts, dosing reminders, and device online/offline state.

### Done criteria for this task
- App lives under `task_iot_automation_04/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_4: Aquarium controller dashboard` and start the next task immediately.

---

## Task 05 — Building HVAC zone manager
**workdir:** `task_iot_automation_05`
**id:** `iot_automation_05_building-hvac-zone-manager`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=cpp, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=multi_turn_repair, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Build an HVAC zone manager: multiple zones with setpoints, schedules, occupancy modes, and energy usage history stubs.

### Done criteria for this task
- App lives under `task_iot_automation_05/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=browser_smoke, tools=mixed)

When done, print `DONE task_5: Building HVAC zone manager` and start the next task immediately.

---

## Task 06 — MQTT device playground
**workdir:** `task_iot_automation_06`
**id:** `iot_automation_06_mqtt-device-playground`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=rust, artifact_type=backend_api, task_family=coding_implement, agent_topology=single_agent, verification_mode=visual_diff, session_shape=approval_gated, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create an MQTT device playground UI + broker stub: subscribe/publish topics, device registry, and rule: if topic X then command Y.

### Done criteria for this task
- App lives under `task_iot_automation_06/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=visual_diff, tools=edit_heavy)

When done, print `DONE task_6: MQTT device playground` and start the next task immediately.

---

## Task 07 — Smart irrigation planner
**workdir:** `task_iot_automation_07`
**id:** `iot_automation_07_smart-irrigation-planner`
**source:** `original`
**dimensions:** complexity=medium, value=low, language_runtime=go, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=single_shot, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Build a smart irrigation planner: zones, soil moisture simulation, weather stub, watering schedules, and manual override.

### Done criteria for this task
- App lives under `task_iot_automation_07/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_7: Smart irrigation planner` and start the next task immediately.

---

## Task 08 — Lab instrument rack monitor
**workdir:** `task_iot_automation_08`
**id:** `iot_automation_08_lab-instrument-rack-monitor`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=java, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=multi_turn_repair, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=empty_scratch

### User request

Create a lab instrument rack monitor: power draw simulation, over-temp alarms, maintenance tickets, and CSV export of readings.

### Done criteria for this task
- App lives under `task_iot_automation_08/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_8: Lab instrument rack monitor` and start the next task immediately.

---

## Task 09 — Home energy meter dashboard
**workdir:** `task_iot_automation_09`
**id:** `iot_automation_09_home-energy-meter-dashboard`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=typescript, artifact_type=web_fullstack, task_family=data_visualization, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=resume_mid_task, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Build a home energy meter dashboard with simulated circuits, daily kWh charts, peak alerts, and appliance grouping.

### Done criteria for this task
- App lives under `task_iot_automation_09/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=browser_smoke, tools=mixed)

When done, print `DONE task_9: Home energy meter dashboard` and start the next task immediately.

---

## Task 10 — Parking lot occupancy sensors
**workdir:** `task_iot_automation_10`
**id:** `iot_automation_10_parking-lot-occupancy-sensors`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=python, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=multi_turn_repair, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a parking lot occupancy system: bay sensors, live map, free-bay counts, and reservation windows.

### Done criteria for this task
- App lives under `task_iot_automation_10/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_10: Parking lot occupancy sensors` and start the next task immediately.

---

## After all 10 (iot_automation)

Print a final summary table: task id | path | stack | complexity | how to run.
Then stop.
