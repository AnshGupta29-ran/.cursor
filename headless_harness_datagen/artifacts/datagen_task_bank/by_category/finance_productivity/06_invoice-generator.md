# Invoice generator

- category: `finance_productivity`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "hard", "language_runtime": "typescript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "finance_fintech"}`

## Seed

Build an invoice generator: clients, line items, tax, PDF/HTML export, and payment status tracking.

## Run (single category pipeline)

```bash
python main.py "Build an invoice generator: clients, line items, tax, PDF/HTML export, and payment status tracking." --forge-prompt --forge-category finance_productivity --workdir task_finance_productivity_06
```
