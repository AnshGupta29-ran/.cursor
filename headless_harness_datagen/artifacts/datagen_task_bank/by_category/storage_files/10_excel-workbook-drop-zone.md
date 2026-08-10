# Excel workbook drop zone

- category: `storage_files`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "excel_office", "artifact_type": "spreadsheet_workbook", "task_family": "spreadsheet_excel", "business_domain": "data_analytics", "modality": "tabular_excel"}`

## Seed

Build a small service that accepts Excel/CSV uploads, validates sheets, stores them, and lists workbook metadata (sheet names, row counts) without requiring MS Office installed.

## Run (single category pipeline)

```bash
python main.py "Build a small service that accepts Excel/CSV uploads, validates sheets, stores them, and lists workbook metadata (sheet names, row counts) without requiring MS Office installed." --forge-prompt --forge-category storage_files --workdir task_storage_files_10
```
