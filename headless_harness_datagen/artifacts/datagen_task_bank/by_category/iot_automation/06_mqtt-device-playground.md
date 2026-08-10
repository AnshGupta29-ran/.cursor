# MQTT device playground

- category: `iot_automation`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "hard", "language_runtime": "go", "artifact_type": "backend_api", "task_family": "coding_implement", "business_domain": "iot_automation"}`

## Seed

Create an MQTT device playground UI + broker stub: subscribe/publish topics, device registry, and rule: if topic X then command Y.

## Run (single category pipeline)

```bash
python main.py "Create an MQTT device playground UI + broker stub: subscribe/publish topics, device registry, and rule: if topic X then command Y." --forge-prompt --forge-category iot_automation --workdir task_iot_automation_06
```
