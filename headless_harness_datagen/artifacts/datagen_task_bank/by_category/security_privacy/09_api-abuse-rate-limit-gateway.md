# API abuse rate-limit gateway

- category: `security_privacy`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "go", "artifact_type": "backend_api", "task_family": "coding_implement", "business_domain": "devops_platform"}`

## Seed

Build a rate-limit gateway middleware/service with token buckets per API key, 429 responses, and metrics.

## Run (single category pipeline)

```bash
python main.py "Build a rate-limit gateway middleware/service with token buckets per API key, 429 responses, and metrics." --forge-prompt --forge-category security_privacy --workdir task_security_privacy_09
```
