# Job board

- category: `generic_fullstack`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "javascript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "general_utilities"}`

## Seed

Create a job board: employer posts, seeker applications, filters, and saved jobs.

## Run (single category pipeline)

```bash
python main.py "Create a job board: employer posts, seeker applications, filters, and saved jobs." --forge-prompt --forge-category generic_fullstack --workdir task_generic_fullstack_05
```
