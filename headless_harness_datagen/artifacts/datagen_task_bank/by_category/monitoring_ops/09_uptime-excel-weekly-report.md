# Uptime Excel weekly report

- category: `monitoring_ops`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "low", "language_runtime": "excel_office", "artifact_type": "spreadsheet_workbook", "task_family": "spreadsheet_excel", "business_domain": "devops_platform", "modality": "tabular_excel"}`

## Seed

Build a tool that reads uptime check CSVs and produces a weekly Excel report with SLO burn and incident list.

## Run (single category pipeline)

```bash
python main.py "Build a tool that reads uptime check CSVs and produces a weekly Excel report with SLO burn and incident list." --forge-prompt --forge-category monitoring_ops --workdir task_monitoring_ops_09
```
