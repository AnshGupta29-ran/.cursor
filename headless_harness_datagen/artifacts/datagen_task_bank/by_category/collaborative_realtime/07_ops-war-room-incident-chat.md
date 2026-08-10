# Ops war-room incident chat

- category: `collaborative_realtime`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "hard", "language_runtime": "go", "artifact_type": "backend_api", "task_family": "coding_implement", "business_domain": "devops_platform"}`

## Seed

Build an incident war-room chat with channels per incident, @mentions, severity tags, and a timeline of status updates synced live.

## Run (single category pipeline)

```bash
python main.py "Build an incident war-room chat with channels per incident, @mentions, severity tags, and a timeline of status updates synced live." --forge-prompt --forge-category collaborative_realtime --workdir task_collaborative_realtime_07
```
