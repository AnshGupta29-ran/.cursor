# Env var & secrets sync tool

- category: `devops_infra`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "python", "artifact_type": "cli_tool", "task_family": "devops_ops", "business_domain": "security_privacy"}`

## Seed

Build an env sync tool: compare .env across environments, redact secrets in diffs, and apply patches.

## Run (single category pipeline)

```bash
python main.py "Build an env sync tool: compare .env across environments, redact secrets in diffs, and apply patches." --forge-prompt --forge-category devops_infra --workdir task_devops_infra_07
```
