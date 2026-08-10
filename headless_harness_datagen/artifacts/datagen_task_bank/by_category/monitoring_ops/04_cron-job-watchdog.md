# Cron job watchdog

- category: `monitoring_ops`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "python", "artifact_type": "backend_api", "task_family": "coding_implement", "business_domain": "devops_platform"}`

## Seed

Build a cron/job watchdog: expected run windows, last-success heartbeats, and missed-run alerts.

## Run (single category pipeline)

```bash
python main.py "Build a cron/job watchdog: expected run windows, last-success heartbeats, and missed-run alerts." --forge-prompt --forge-category monitoring_ops --workdir task_monitoring_ops_04
```
