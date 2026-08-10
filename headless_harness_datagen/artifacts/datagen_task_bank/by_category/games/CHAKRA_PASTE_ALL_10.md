# Category batch: games (all 10) — paste into Chakra

You are running a **datagen category marathon** for harness evaluation.
Category focus: **browser/desktop games — playable UI required**.

## Non-negotiable rules

1. Complete the **10 tasks below in order** (01 → 10). Do not skip.
2. Each task is a **separate app/project** under its own folder `task_games_NN/` (use the workdir listed).
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

Tag every DONE note with category `games` so logs are easy to grep.

---

## Task 01 — Breakout clone with levels
**workdir:** `task_games_01`
**id:** `games_01_breakout-clone-with-levels`
**source:** `original`
**dimensions:** complexity=medium, value=low, language_runtime=python, artifact_type=game_prototype, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=single_shot, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Create a Breakout/Arkanoid clone in Python + Pygame with multiple levels, power-ups, lives, high scores, and pause.

### Done criteria for this task
- App lives under `task_games_01/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_1: Breakout clone with levels` and start the next task immediately.

---

## Task 02 — Turn-based tactics grid
**workdir:** `task_games_02`
**id:** `games_02_turn-based-tactics-grid`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=typescript, artifact_type=game_prototype, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=multi_turn_repair, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=empty_scratch

### User request

Build a small turn-based tactics game on a grid: two units sides, move/attack, cover tiles, and win/lose conditions.

### Done criteria for this task
- App lives under `task_games_02/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_2: Turn-based tactics grid` and start the next task immediately.

---

## Task 03 — Endless runner
**workdir:** `task_games_03`
**id:** `games_03_endless-runner`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=javascript, artifact_type=game_prototype, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=resume_mid_task, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Create an endless runner with procedural obstacles, score distance, difficulty ramp, and restart flow (canvas or Pygame).

### Done criteria for this task
- App lives under `task_games_03/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=browser_smoke, tools=mixed)

When done, print `DONE task_3: Endless runner` and start the next task immediately.

---

## Task 04 — Minesweeper with solver hint
**workdir:** `task_games_04`
**id:** `games_04_minesweeper-with-solver-hint`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=csharp, artifact_type=game_prototype, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=multi_turn_repair, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Build Minesweeper with difficulty presets and a hint mode that highlights a safe deduction when possible.

### Done criteria for this task
- App lives under `task_games_04/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_4: Minesweeper with solver hint` and start the next task immediately.

---

## Task 05 — Card battler prototype
**workdir:** `task_games_05`
**id:** `games_05_card-battler-prototype`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=cpp, artifact_type=game_prototype, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=approval_gated, tool_profile=mixed, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Create a simple collectible card battler: deck, draw, mana, and a basic AI opponent turn.

### Done criteria for this task
- App lives under `task_games_05/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=mixed)

When done, print `DONE task_5: Card battler prototype` and start the next task immediately.

---

## Task 06 — Physics sandbox balls
**workdir:** `task_games_06`
**id:** `games_06_physics-sandbox-balls`
**source:** `original`
**dimensions:** complexity=low, value=low, language_runtime=rust, artifact_type=game_prototype, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=single_shot, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Build a 2D physics sandbox with spawnable balls, gravity toggle, and collision counters (box2d or simple physics).

### Done criteria for this task
- App lives under `task_games_06/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_6: Physics sandbox balls` and start the next task immediately.

---

## Task 07 — Typing race multiplayer local
**workdir:** `task_games_07`
**id:** `games_07_typing-race-multiplayer-local`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=javascript, artifact_type=game_prototype, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=multi_turn_repair, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=empty_scratch

### User request

Create a local multiplayer typing race: shared prompt, per-player progress bars, WPM, and winner screen.

### Done criteria for this task
- App lives under `task_games_07/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_7: Typing race multiplayer local` and start the next task immediately.

---

## Task 08 — Roguelike ASCII dungeon
**workdir:** `task_games_08`
**id:** `games_08_roguelike-ascii-dungeon`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=typescript, artifact_type=game_prototype, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=resume_mid_task, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=partial_scaffold

### User request

Implement a small ASCII roguelike: procedural rooms, fog of war, enemies, inventory of 3 items, and save.

### Done criteria for this task
- App lives under `task_games_08/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_8: Roguelike ASCII dungeon` and start the next task immediately.

---

## Task 09 — Puzzle match-3 lite
**workdir:** `task_games_09`
**id:** `games_09_puzzle-match-3-lite`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=python, artifact_type=game_prototype, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=multi_turn_repair, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Build a match-3 puzzle lite with board swap, cascades, score targets, and limited moves.

### Done criteria for this task
- App lives under `task_games_09/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=browser_smoke, tools=mixed)

When done, print `DONE task_9: Puzzle match-3 lite` and start the next task immediately.

---

## Task 10 — Simulated stock trading game
**workdir:** `task_games_10`
**id:** `games_10_simulated-stock-trading-game`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=go, artifact_type=game_prototype, task_family=coding_implement, agent_topology=single_agent, verification_mode=visual_diff, session_shape=approval_gated, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a stock trading simulation game: fake price series, buy/sell portfolio, leaderboard of profit.

### Done criteria for this task
- App lives under `task_games_10/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=visual_diff, tools=edit_heavy)

When done, print `DONE task_10: Simulated stock trading game` and start the next task immediately.

---

## After all 10 (games)

Print a final summary table: task id | path | stack | complexity | how to run.
Then stop.
