# Shared music listening room

- category: `collaborative_realtime`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "javascript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "media_cms"}`

## Seed

Create a synchronized listening room: queue tracks, play/pause sync across clients, chat, and host controls.

## Run (single category pipeline)

```bash
python main.py "Create a synchronized listening room: queue tracks, play/pause sync across clients, chat, and host controls." --forge-prompt --forge-category collaborative_realtime --workdir task_collaborative_realtime_08
```
