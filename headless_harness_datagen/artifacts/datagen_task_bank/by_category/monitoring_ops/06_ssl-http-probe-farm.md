# SSL/HTTP probe farm

- category: `monitoring_ops`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "javascript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "devops_platform"}`

## Seed

Create an HTTP probe farm: configured URLs, expected status codes, latency SLOs, and failure screenshots stubs.

## Run (single category pipeline)

```bash
python main.py "Create an HTTP probe farm: configured URLs, expected status codes, latency SLOs, and failure screenshots stubs." --forge-prompt --forge-category monitoring_ops --workdir task_monitoring_ops_06
```
