# Newsroom editorial desk

- category: `cms_content`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "csharp", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "media_cms"}`

## Seed

Build a newsroom desk: story assignments, statuses (pitch→edit→publish), embargo times, and role-based access.

## Run (single category pipeline)

```bash
python main.py "Build a newsroom desk: story assignments, statuses (pitch\u2192edit\u2192publish), embargo times, and role-based access." --forge-prompt --forge-category cms_content --workdir task_cms_content_09
```
