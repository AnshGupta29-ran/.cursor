# Embedding search for FAQs

- category: `ai_ml`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "hard", "language_runtime": "python", "artifact_type": "backend_api", "task_family": "ml_inference_eval", "business_domain": "general_utilities"}`

## Seed

Create an FAQ semantic search API using local embeddings (or TF-IDF fallback), with admin CRUD for FAQ entries and ranked answers.

## Run (single category pipeline)

```bash
python main.py "Create an FAQ semantic search API using local embeddings (or TF-IDF fallback), with admin CRUD for FAQ entries and ranked answers." --forge-prompt --forge-category ai_ml --workdir task_ai_ml_07
```
