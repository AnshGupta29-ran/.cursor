# AI document assistant

- category: `ai_ml`
- source: `archive:python_13`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "ml_inference_eval", "business_domain": "productivity_collab"}`

## Seed

Build an AI Document Assistant: upload text/PDF, chunk and index locally, answer questions with citations from retrieved chunks (stub LLM OK if labeled).

## Run (single category pipeline)

```bash
python main.py "Build an AI Document Assistant: upload text/PDF, chunk and index locally, answer questions with citations from retrieved chunks (stub LLM OK if labeled)." --forge-prompt --forge-category ai_ml --workdir task_ai_ml_04
```
