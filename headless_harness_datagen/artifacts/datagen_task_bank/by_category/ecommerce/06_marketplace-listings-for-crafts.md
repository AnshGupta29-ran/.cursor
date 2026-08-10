# Marketplace listings for crafts

- category: `ecommerce`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "ecommerce"}`

## Seed

Build a craft marketplace: seller listings, buyer search/filters, orders, and simple ratings.

## Run (single category pipeline)

```bash
python main.py "Build a craft marketplace: seller listings, buyer search/filters, orders, and simple ratings." --forge-prompt --forge-category ecommerce --workdir task_ecommerce_06
```
