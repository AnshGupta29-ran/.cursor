# AI Resume Analyzer

- category: `ai_ml`
- source: `archive:4`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "python", "artifact_type": "web_fullstack", "task_family": "ml_inference_eval", "business_domain": "data_analytics"}`

## Seed

Create a resume analysis web application using React, FastAPI, and a pre-trained NLP model from Hugging Face Transformers. Users should be able to upload PDF or DOCX resumes, extract structured information, identify skills, estimate experience level, and compare the resume against a provided job description. Display skill gaps, matching percentage, keyword analysis, and recommendations through an intuitive dashboard.

## Run (single category pipeline)

```bash
python main.py "Create a resume analysis web application using React, FastAPI, and a pre-trained NLP model from Hugging Face Transformers. Users should be able to upload PDF or DOCX resumes, extract structured information, identify skills, estimate experience level, and compare the resume against a provided job description. Display skill gaps, matching percentage, keyword analysis, and recommendations through an intuitive dashboard." --forge-prompt --forge-category ai_ml --workdir task_ai_ml_01
```
