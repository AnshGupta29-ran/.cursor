# Documentation portal versioned

- category: `cms_content`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "go", "artifact_type": "web_fullstack", "task_family": "documentation", "business_domain": "devops_platform"}`

## Seed

Create a versioned docs portal (v1/v2), markdown pages, sidebar nav, and search across versions.

## Run (single category pipeline)

```bash
python main.py "Create a versioned docs portal (v1/v2), markdown pages, sidebar nav, and search across versions." --forge-prompt --forge-category cms_content --workdir task_cms_content_10
```
