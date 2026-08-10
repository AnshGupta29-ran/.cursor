# Returns and RMA portal

- category: `ecommerce`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "csharp", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "ecommerce"}`

## Seed

Create a returns/RMA portal: request return, reasons, approval workflow, and refund status tracking.

## Run (single category pipeline)

```bash
python main.py "Create a returns/RMA portal: request return, reasons, approval workflow, and refund status tracking." --forge-prompt --forge-category ecommerce --workdir task_ecommerce_08
```
