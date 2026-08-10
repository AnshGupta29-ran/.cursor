# Internal wiki with approvals

- category: `cms_content`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "hard", "language_runtime": "java", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "productivity_collab"}`

## Seed

Create an internal company wiki with page hierarchy, edit approvals, and change history diffs.

## Run (single category pipeline)

```bash
python main.py "Create an internal company wiki with page hierarchy, edit approvals, and change history diffs." --forge-prompt --forge-category cms_content --workdir task_cms_content_06
```
