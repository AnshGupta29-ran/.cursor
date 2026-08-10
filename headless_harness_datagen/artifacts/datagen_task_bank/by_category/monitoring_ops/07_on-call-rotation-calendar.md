# On-call rotation calendar

- category: `monitoring_ops`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "typescript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "devops_platform"}`

## Seed

Build an on-call rotation calendar with schedules, overrides, and alert routing contact list (no real PagerDuty).

## Run (single category pipeline)

```bash
python main.py "Build an on-call rotation calendar with schedules, overrides, and alert routing contact list (no real PagerDuty)." --forge-prompt --forge-category monitoring_ops --workdir task_monitoring_ops_07
```
