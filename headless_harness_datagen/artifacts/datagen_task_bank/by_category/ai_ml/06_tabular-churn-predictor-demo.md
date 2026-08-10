# Tabular churn predictor demo

- category: `ai_ml`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "python", "artifact_type": "notebook_analysis", "task_family": "data_wrangling", "business_domain": "finance_fintech", "modality": "tabular_excel"}`

## Seed

Build a churn prediction demo: upload CSV, train a simple sklearn model, show feature importances, and predict on new rows.

## Run (single category pipeline)

```bash
python main.py "Build a churn prediction demo: upload CSV, train a simple sklearn model, show feature importances, and predict on new rows." --forge-prompt --forge-category ai_ml --workdir task_ai_ml_06
```
