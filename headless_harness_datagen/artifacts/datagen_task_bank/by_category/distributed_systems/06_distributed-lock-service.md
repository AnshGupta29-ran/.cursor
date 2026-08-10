# Distributed lock service

- category: `distributed_systems`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "go", "artifact_type": "backend_api", "task_family": "coding_implement", "business_domain": "devops_platform"}`

## Seed

Implement a distributed lock service API with TTL, fencing tokens, and contention tests.

## Run (single category pipeline)

```bash
python main.py "Implement a distributed lock service API with TTL, fencing tokens, and contention tests." --forge-prompt --forge-category distributed_systems --workdir task_distributed_systems_06
```
