# Live CSV co-editing sheet

- category: `collaborative_realtime`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "typescript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "data_analytics", "modality": "tabular_excel"}`

## Seed

Build a lightweight collaborative spreadsheet for CSV data with cell editing, live sync, and conflict highlighting (not Excel-plugin).

## Run (single category pipeline)

```bash
python main.py "Build a lightweight collaborative spreadsheet for CSV data with cell editing, live sync, and conflict highlighting (not Excel-plugin)." --forge-prompt --forge-category collaborative_realtime --workdir task_collaborative_realtime_09
```
