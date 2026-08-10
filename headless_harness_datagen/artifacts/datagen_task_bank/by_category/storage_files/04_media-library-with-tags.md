# Media library with tags

- category: `storage_files`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "python", "artifact_type": "backend_api", "task_family": "coding_implement", "business_domain": "media_cms"}`

## Seed

Create a media library service for images and videos: upload, tag, search, thumbnail generation stubs, and collections.

## Run (single category pipeline)

```bash
python main.py "Create a media library service for images and videos: upload, tag, search, thumbnail generation stubs, and collections." --forge-prompt --forge-category storage_files --workdir task_storage_files_04
```
