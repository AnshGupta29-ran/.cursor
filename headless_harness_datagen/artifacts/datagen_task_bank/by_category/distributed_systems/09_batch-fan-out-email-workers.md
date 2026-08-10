# Batch fan-out email workers

- category: `distributed_systems`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "javascript", "artifact_type": "backend_api", "task_family": "coding_implement", "business_domain": "media_cms"}`

## Seed

Create a fan-out email sending simulator: enqueue campaigns, workers send stubs, track delivery states.

## Run (single category pipeline)

```bash
python main.py "Create a fan-out email sending simulator: enqueue campaigns, workers send stubs, track delivery states." --forge-prompt --forge-category distributed_systems --workdir task_distributed_systems_09
```
