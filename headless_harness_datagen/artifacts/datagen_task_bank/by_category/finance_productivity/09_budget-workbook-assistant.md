# Budget workbook assistant

- category: `finance_productivity`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "excel_office", "artifact_type": "spreadsheet_workbook", "task_family": "spreadsheet_excel", "business_domain": "finance_fintech", "modality": "tabular_excel"}`

## Seed

Create a budget workbook assistant that generates and updates an Excel monthly budget with categories and variance formulas.

## Run (single category pipeline)

```bash
python main.py "Create a budget workbook assistant that generates and updates an Excel monthly budget with categories and variance formulas." --forge-prompt --forge-category finance_productivity --workdir task_finance_productivity_09
```
