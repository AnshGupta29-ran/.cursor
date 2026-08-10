# Multiplayer kanban board live sync

- category: `collaborative_realtime`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "typescript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "productivity_collab"}`

## Seed

Create a multiplayer kanban board where cards and columns sync in real time across users with presence indicators, conflict-safe moves, and room-based boards.

## Run (single category pipeline)

```bash
python main.py "Create a multiplayer kanban board where cards and columns sync in real time across users with presence indicators, conflict-safe moves, and room-based boards." --forge-prompt --forge-category collaborative_realtime --workdir task_collaborative_realtime_02
```
