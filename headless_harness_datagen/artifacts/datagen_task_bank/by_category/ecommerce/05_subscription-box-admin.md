# Subscription box admin

- category: `ecommerce`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "hard", "language_runtime": "typescript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "ecommerce"}`

## Seed

Create a subscription-box admin: plans, subscriber list, skip/pause months, and fulfillment export CSV.

## Run (single category pipeline)

```bash
python main.py "Create a subscription-box admin: plans, subscriber list, skip/pause months, and fulfillment export CSV." --forge-prompt --forge-category ecommerce --workdir task_ecommerce_05
```
