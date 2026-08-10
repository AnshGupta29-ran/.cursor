# Remote design critique board

- category: `collaborative_realtime`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "media_cms"}`

## Seed

Create a real-time design critique board: upload images, pin comments with coordinates, resolve threads, and show live viewers.

## Run (single category pipeline)

```bash
python main.py "Create a real-time design critique board: upload images, pin comments with coordinates, resolve threads, and show live viewers." --forge-prompt --forge-category collaborative_realtime --workdir task_collaborative_realtime_10
```
