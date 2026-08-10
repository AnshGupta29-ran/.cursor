# CAD drawing document locker

- category: `storage_files`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "medium", "language_runtime": "java", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "logistics_ops"}`

## Seed

Create a document locker for engineering drawings: check-in/check-out, revision numbers, and lock ownership.

## Run (single category pipeline)

```bash
python main.py "Create a document locker for engineering drawings: check-in/check-out, revision numbers, and lock ownership." --forge-prompt --forge-category storage_files --workdir task_storage_files_09
```
