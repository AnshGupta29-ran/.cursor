# Terraform state explorer

- category: `devops_infra`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "hard", "language_runtime": "python", "artifact_type": "cli_tool", "task_family": "devops_ops", "business_domain": "devops_platform"}`

## Seed

Build a Terraform state explorer: load state JSON, list resources, show attributes, and diff two state files.

## Run (single category pipeline)

```bash
python main.py "Build a Terraform state explorer: load state JSON, list resources, show attributes, and diff two state files." --forge-prompt --forge-category devops_infra --workdir task_devops_infra_05
```
