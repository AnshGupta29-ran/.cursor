# Wholesale price list Excel sync

- category: `ecommerce`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "excel_office", "artifact_type": "spreadsheet_workbook", "task_family": "spreadsheet_excel", "business_domain": "ecommerce", "modality": "tabular_excel"}`

## Seed

Build a wholesale price-list tool that imports/exports Excel price sheets and applies tier pricing to an in-app catalog.

## Run (single category pipeline)

```bash
python main.py "Build a wholesale price-list tool that imports/exports Excel price sheets and applies tier pricing to an in-app catalog." --forge-prompt --forge-category ecommerce --workdir task_ecommerce_09
```
