# Personal finance tracker PRD

- category: `finance_productivity`
- source: `archive:finance_prd`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "finance_fintech"}`

## Seed

Build a production-quality Personal Finance Tracker application from scratch. The application should allow users to manage their personal finances, track spending habits, and visualize their financial health through an intuitive interface. Support registration/auth, isolated user data, income/expense CRUD, categories, budgets, monthly/yearly summaries, dashboard charts, search/filter, and tests plus README.

## Run (single category pipeline)

```bash
python main.py "Build a production-quality Personal Finance Tracker application from scratch. The application should allow users to manage their personal finances, track spending habits, and visualize their financial health through an intuitive interface. Support registration/auth, isolated user data, income/expense CRUD, categories, budgets, monthly/yearly summaries, dashboard charts, search/filter, and tests plus README." --forge-prompt --forge-category finance_productivity --workdir task_finance_productivity_01
```
