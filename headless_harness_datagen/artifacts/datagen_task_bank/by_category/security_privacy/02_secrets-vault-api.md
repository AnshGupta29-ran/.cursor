# Secrets vault API

- category: `security_privacy`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "go", "artifact_type": "backend_api", "task_family": "security_audit", "business_domain": "security_privacy"}`

## Seed

Build a secrets vault HTTP API: store sealed secrets, role-based read, audit log, and rotation metadata (no plaintext at rest).

## Run (single category pipeline)

```bash
python main.py "Build a secrets vault HTTP API: store sealed secrets, role-based read, audit log, and rotation metadata (no plaintext at rest)." --forge-prompt --forge-category security_privacy --workdir task_security_privacy_02
```
