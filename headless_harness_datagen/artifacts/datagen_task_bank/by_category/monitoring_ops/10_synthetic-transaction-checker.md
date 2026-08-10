# Synthetic transaction checker

- category: `monitoring_ops`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "python", "artifact_type": "cli_tool", "task_family": "testing_qa", "business_domain": "ecommerce"}`

## Seed

Implement a synthetic login→search→checkout transaction checker with step timings and pass/fail reports.

## Run (single category pipeline)

```bash
python main.py "Implement a synthetic login\u2192search\u2192checkout transaction checker with step timings and pass/fail reports." --forge-prompt --forge-category monitoring_ops --workdir task_monitoring_ops_10
```
