# Clock skew demo + NTP stub

- category: `distributed_systems`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "python", "artifact_type": "cli_tool", "task_family": "analysis_reason", "business_domain": "devops_platform"}`

## Seed

Build a multi-node clock skew demo showing logical clocks/vector clocks for event ordering.

## Run (single category pipeline)

```bash
python main.py "Build a multi-node clock skew demo showing logical clocks/vector clocks for event ordering." --forge-prompt --forge-category distributed_systems --workdir task_distributed_systems_10
```
