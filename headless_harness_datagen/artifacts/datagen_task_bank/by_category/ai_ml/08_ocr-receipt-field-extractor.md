# OCR receipt field extractor

- category: `ai_ml`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "medium", "value": "medium", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "ml_inference_eval", "business_domain": "finance_fintech", "modality": "image_vision"}`

## Seed

Build a receipt field extractor: accept images, stub OCR to text if needed, parse merchant/date/total with rules, and return structured JSON + UI review.

## Run (single category pipeline)

```bash
python main.py "Build a receipt field extractor: accept images, stub OCR to text if needed, parse merchant/date/total with rules, and return structured JSON + UI review." --forge-prompt --forge-category ai_ml --workdir task_ai_ml_08
```
