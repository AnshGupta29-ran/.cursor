# Mini cloud storage platform

- category: `storage_files`
- source: `archive:2`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "javascript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "general_utilities"}`

## Seed

Create a cloud storage web application using React, Node.js, Express, and MongoDB. Users should be able to register, log in, upload files, organize them into folders, rename, move, delete, search, and download files. Implement JWT-based authentication, file size validation, storage usage statistics, and a clean dashboard.

## Run (single category pipeline)

```bash
python main.py "Create a cloud storage web application using React, Node.js, Express, and MongoDB. Users should be able to register, log in, upload files, organize them into folders, rename, move, delete, search, and download files. Implement JWT-based authentication, file size validation, storage usage statistics, and a clean dashboard." --forge-prompt --forge-category storage_files --workdir task_storage_files_01
```
