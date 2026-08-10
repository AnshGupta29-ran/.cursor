# Time-series anomaly flagger

- category: `ai_ml`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "python", "artifact_type": "cli_tool", "task_family": "data_visualization", "business_domain": "devops_platform"}`

## Seed

Create a time-series anomaly flagger: ingest metric CSV, detect spikes with z-score/IQR, plot anomalies, and export flagged windows.

## Run (single category pipeline)

```bash
python main.py "Create a time-series anomaly flagger: ingest metric CSV, detect spikes with z-score/IQR, plot anomalies, and export flagged windows." --forge-prompt --forge-category ai_ml --workdir task_ai_ml_10
```
