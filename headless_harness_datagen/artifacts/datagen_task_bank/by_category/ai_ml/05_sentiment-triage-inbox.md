# Sentiment triage inbox

- category: `ai_ml`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "python", "artifact_type": "backend_api", "task_family": "ml_inference_eval", "business_domain": "social_comms"}`

## Seed

Create a support inbox that classifies message sentiment/urgency with a small local model or lexicon baseline and routes tickets to queues.

## Run (single category pipeline)

```bash
python main.py "Create a support inbox that classifies message sentiment/urgency with a small local model or lexicon baseline and routes tickets to queues." --forge-prompt --forge-category ai_ml --workdir task_ai_ml_05
```
