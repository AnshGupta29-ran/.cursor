# Queue depth observatory

- category: `monitoring_ops`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "hard", "language_runtime": "java", "artifact_type": "web_fullstack", "task_family": "data_visualization", "business_domain": "devops_platform"}`

## Seed

Create a queue-depth observatory for fake workers: publish lag metrics, backlog charts, and saturation warnings.

## Run (single category pipeline)

```bash
python main.py "Create a queue-depth observatory for fake workers: publish lag metrics, backlog charts, and saturation warnings." --forge-prompt --forge-category monitoring_ops --workdir task_monitoring_ops_08
```
