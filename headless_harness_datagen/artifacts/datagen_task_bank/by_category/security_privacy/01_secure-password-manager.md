# Secure password manager

- category: `security_privacy`
- source: `archive:6`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "python", "artifact_type": "desktop_app", "task_family": "coding_implement", "business_domain": "security_privacy"}`

## Seed

Create a desktop password manager using Python and PySide6 (Qt). Users should be able to create encrypted password vaults protected by a master password. Implement AES encryption, password generation, categories, search, clipboard copying with automatic clearing, password strength indicators, and secure import/export functionality. Include proper exception handling and unit tests for the encryption logic.

## Run (single category pipeline)

```bash
python main.py "Create a desktop password manager using Python and PySide6 (Qt). Users should be able to create encrypted password vaults protected by a master password. Implement AES encryption, password generation, categories, search, clipboard copying with automatic clearing, password strength indicators, and secure import/export functionality. Include proper exception handling and unit tests for the encryption logic." --forge-prompt --forge-category security_privacy --workdir task_security_privacy_01
```
