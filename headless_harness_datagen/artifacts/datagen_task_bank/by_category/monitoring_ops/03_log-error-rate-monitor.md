# Log error rate monitor

- category: `monitoring_ops`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "go", "artifact_type": "cli_tool", "task_family": "coding_implement", "business_domain": "devops_platform", "modality": "logs_telemetry"}`

## Seed

Create a log tail monitor that counts error patterns, charts rates, and fires threshold alerts.

## Run (single category pipeline)

```bash
python main.py "Create a log tail monitor that counts error patterns, charts rates, and fires threshold alerts." --forge-prompt --forge-category monitoring_ops --workdir task_monitoring_ops_03
```
