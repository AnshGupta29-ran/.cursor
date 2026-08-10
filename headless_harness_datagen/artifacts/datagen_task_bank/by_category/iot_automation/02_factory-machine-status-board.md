# Factory machine status board

- category: `iot_automation`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "typescript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "iot_automation"}`

## Seed

Create a factory machine status board with simulated PLC devices, downtime reasons, OEE-style metrics, and operator acknowledgements.

## Run (single category pipeline)

```bash
python main.py "Create a factory machine status board with simulated PLC devices, downtime reasons, OEE-style metrics, and operator acknowledgements." --forge-prompt --forge-category iot_automation --workdir task_iot_automation_02
```
