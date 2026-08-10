# Pair programming shared editor

- category: `collaborative_realtime`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "medium", "language_runtime": "javascript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "education"}`

## Seed

Build a pair-programming web app with a shared code editor, cursors for each user, chat sidebar, and session links. Use WebSockets for sync.

## Run (single category pipeline)

```bash
python main.py "Build a pair-programming web app with a shared code editor, cursors for each user, chat sidebar, and session links. Use WebSockets for sync." --forge-prompt --forge-category collaborative_realtime --workdir task_collaborative_realtime_03
```
