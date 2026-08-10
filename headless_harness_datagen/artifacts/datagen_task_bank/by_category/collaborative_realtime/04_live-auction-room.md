# Live auction room

- category: `collaborative_realtime`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "hard", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "ecommerce"}`

## Seed

Create a real-time auction room platform: users join rooms, place bids, see live bid feed and countdown timers, and get notified when outbid.

## Run (single category pipeline)

```bash
python main.py "Create a real-time auction room platform: users join rooms, place bids, see live bid feed and countdown timers, and get notified when outbid." --forge-prompt --forge-category collaborative_realtime --workdir task_collaborative_realtime_04
```
