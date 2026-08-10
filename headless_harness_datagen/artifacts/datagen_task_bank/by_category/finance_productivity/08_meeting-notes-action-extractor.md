# Meeting notes action extractor

- category: `finance_productivity`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "analysis_reason", "business_domain": "productivity_collab"}`

## Seed

Build a meeting-notes tool that stores notes and extracts action items with owners/due dates (rules or light NLP).

## Run (single category pipeline)

```bash
python main.py "Build a meeting-notes tool that stores notes and extracts action items with owners/due dates (rules or light NLP)." --forge-prompt --forge-category finance_productivity --workdir task_finance_productivity_08
```
