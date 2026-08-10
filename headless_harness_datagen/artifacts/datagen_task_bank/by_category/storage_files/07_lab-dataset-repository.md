# Lab dataset repository

- category: `storage_files`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "data_analytics"}`

## Seed

Create a research dataset repository: upload zipped datasets, metadata forms, license tags, and download permissions by role.

## Run (single category pipeline)

```bash
python main.py "Create a research dataset repository: upload zipped datasets, metadata forms, license tags, and download permissions by role." --forge-prompt --forge-category storage_files --workdir task_storage_files_07
```
