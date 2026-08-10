# Network monitoring dashboard

- category: `monitoring_ops`
- source: `archive:8`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "devops_platform"}`

## Seed

Create a network monitoring application using Python and FastAPI. The backend should periodically ping configurable hosts, measure response times, detect outages, and expose REST APIs for historical metrics. Build a React dashboard that visualizes uptime percentages, latency graphs, downtime history, and device health using interactive charts. Support configurable monitoring intervals and persistent storage using SQLite.

## Run (single category pipeline)

```bash
python main.py "Create a network monitoring application using Python and FastAPI. The backend should periodically ping configurable hosts, measure response times, detect outages, and expose REST APIs for historical metrics. Build a React dashboard that visualizes uptime percentages, latency graphs, downtime history, and device health using interactive charts. Support configurable monitoring intervals and persistent storage using SQLite." --forge-prompt --forge-category monitoring_ops --workdir task_monitoring_ops_01
```
