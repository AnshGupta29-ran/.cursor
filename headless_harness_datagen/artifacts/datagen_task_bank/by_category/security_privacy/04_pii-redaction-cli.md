# PII redaction CLI

- category: `security_privacy`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "python", "artifact_type": "cli_tool", "task_family": "security_audit", "business_domain": "legal_compliance"}`

## Seed

Implement a PII redaction CLI that scans text/CSV for emails/phones/SSNs and writes redacted copies with a report.

## Run (single category pipeline)

```bash
python main.py "Implement a PII redaction CLI that scans text/CSV for emails/phones/SSNs and writes redacted copies with a report." --forge-prompt --forge-category security_privacy --workdir task_security_privacy_04
```
