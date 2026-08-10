# Bike shop merchant catalog

- category: `ecommerce`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "javascript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "ecommerce"}`

## Seed

Build a bike shop merchant catalog with variants (size/color), inventory counts, and checkout cart (no payment processor required).

## Run (single category pipeline)

```bash
python main.py "Build a bike shop merchant catalog with variants (size/color), inventory counts, and checkout cart (no payment processor required)." --forge-prompt --forge-category ecommerce --workdir task_ecommerce_04
```
