# 2FA login playground

- category: `security_privacy`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "hard", "language_runtime": "typescript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "security_privacy"}`

## Seed

Create an auth playground with password login, TOTP 2FA enrollment, backup codes, and session management.

## Run (single category pipeline)

```bash
python main.py "Create an auth playground with password login, TOTP 2FA enrollment, backup codes, and session management." --forge-prompt --forge-category security_privacy --workdir task_security_privacy_03
```
