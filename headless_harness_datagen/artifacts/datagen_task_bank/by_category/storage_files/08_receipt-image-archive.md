# Receipt image archive

- category: `storage_files`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "typescript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "finance_fintech"}`

## Seed

Build a receipt/image archive with folders by month, OCR-ready file naming, search by filename/tags, and bulk export.

## Run (single category pipeline)

```bash
python main.py "Build a receipt/image archive with folders by month, OCR-ready file naming, search by filename/tags, and bulk export." --forge-prompt --forge-category storage_files --workdir task_storage_files_08
```
