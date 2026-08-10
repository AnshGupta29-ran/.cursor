# Disk and memory host agent

- category: `monitoring_ops`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "rust", "artifact_type": "cli_tool", "task_family": "coding_implement", "business_domain": "devops_platform"}`

## Seed

Implement a local host agent that samples CPU/mem/disk and pushes metrics to a small collector UI.

## Run (single category pipeline)

```bash
python main.py "Implement a local host agent that samples CPU/mem/disk and pushes metrics to a small collector UI." --forge-prompt --forge-category monitoring_ops --workdir task_monitoring_ops_05
```
