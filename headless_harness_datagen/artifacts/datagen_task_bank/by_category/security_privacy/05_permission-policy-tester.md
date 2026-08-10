# Permission policy tester

- category: `security_privacy`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "java", "artifact_type": "cli_tool", "task_family": "security_audit", "business_domain": "security_privacy"}`

## Seed

Build a RBAC/ABAC policy tester: define roles/permissions, evaluate access queries, and show allow/deny with reasons.

## Run (single category pipeline)

```bash
python main.py "Build a RBAC/ABAC policy tester: define roles/permissions, evaluate access queries, and show allow/deny with reasons." --forge-prompt --forge-category security_privacy --workdir task_security_privacy_05
```
