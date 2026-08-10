# Local registry + image GC

- category: `devops_infra`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "rust", "artifact_type": "backend_api", "task_family": "devops_ops", "business_domain": "devops_platform"}`

## Seed

Create a local container image registry stub with tag list, delete, and garbage-collection policy demo.

## Run (single category pipeline)

```bash
python main.py "Create a local container image registry stub with tag list, delete, and garbage-collection policy demo." --forge-prompt --forge-category devops_infra --workdir task_devops_infra_06
```
