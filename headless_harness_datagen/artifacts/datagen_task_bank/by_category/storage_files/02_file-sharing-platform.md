# File sharing platform

- category: `storage_files`
- source: `archive:python_7`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "general_utilities"}`

## Seed

Create a File Sharing Platform in Python: users upload files, get shareable links with optional expiry and password, track download counts, and manage their uploads via a simple web UI.

## Run (single category pipeline)

```bash
python main.py "Create a File Sharing Platform in Python: users upload files, get shareable links with optional expiry and password, track download counts, and manage their uploads via a simple web UI." --forge-prompt --forge-category storage_files --workdir task_storage_files_02
```
