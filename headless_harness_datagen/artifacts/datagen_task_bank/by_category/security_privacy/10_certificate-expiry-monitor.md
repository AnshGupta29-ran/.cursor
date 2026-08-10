# Certificate expiry monitor

- category: `security_privacy`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "security_privacy"}`

## Seed

Create a TLS certificate expiry monitor: check hosts, store notAfter dates, alert when within N days, simple dashboard.

## Run (single category pipeline)

```bash
python main.py "Create a TLS certificate expiry monitor: check hosts, store notAfter dates, alert when within N days, simple dashboard." --forge-prompt --forge-category security_privacy --workdir task_security_privacy_10
```
