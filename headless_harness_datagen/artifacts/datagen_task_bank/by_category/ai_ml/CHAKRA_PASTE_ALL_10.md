# Category batch: ai_ml (all 10) — paste into Chakra

You are running a **datagen category marathon** for harness evaluation.
Category focus: **AI/ML apps — trainable or inferable demo with clear outputs**.

## Non-negotiable rules

1. Complete the **10 tasks below in order** (01 → 10). Do not skip.
2. Each task is a **separate app/project** under its own folder `task_ai_ml_NN/` (use the workdir listed).
3. For each task: implement until **demoable** (browser open, CLI works, or game playable). Install deps, start servers, fix bugs.
4. **Do not ask for approval** between tasks — continue automatically.
5. After each task: short note `DONE task_N: <title> — path + how to run`.
6. **Vary implementation** across tasks — different stacks/patterns matching the dimension targets. Do not clone the same scaffold 10 times.
7. Challenge the harness: use tools, tests, browser checks, repairs when dims say so.
8. Prefer completing a solid MVP over endless polish; then move to the next task.

## Stats / ledger

Keep the stats site running once (`python -m prompt_stats serve`).
Open http://127.0.0.1:8787/ — hard-refresh the page to pull latest Chakra
sessions into the dashboard (no separate `collect` command).

Tag every DONE note with category `ai_ml` so logs are easy to grep.

---

## Task 01 — AI Resume Analyzer
**workdir:** `task_ai_ml_01`
**id:** `ai_ml_01_ai-resume-analyzer`
**source:** `archive:4`
**dimensions:** complexity=medium, value=medium, language_runtime=python, artifact_type=web_fullstack, task_family=ml_inference_eval, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=multi_turn_repair, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=empty_scratch

### User request

Create a resume analysis web application using React, FastAPI, and a pre-trained NLP model from Hugging Face Transformers. Users should be able to upload PDF or DOCX resumes, extract structured information, identify skills, estimate experience level, and compare the resume against a provided job description. Display skill gaps, matching percentage, keyword analysis, and recommendations through an intuitive dashboard.

### Done criteria for this task
- App lives under `task_ai_ml_01/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_1: AI Resume Analyzer` and start the next task immediately.

---

## Task 02 — ML experiment tracking (MLflow-like)
**workdir:** `task_ai_ml_02`
**id:** `ai_ml_02_ml-experiment-tracking-mlflow-like`
**source:** `archive:bonus`
**dimensions:** complexity=hard, value=hard, language_runtime=python, artifact_type=web_fullstack, task_family=ml_inference_eval, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=resume_mid_task, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=partial_scaffold

### User request

Build a machine learning experiment tracking platform similar to MLflow with experiment comparison, metric visualization, artifact storage, and REST APIs.

### Done criteria for this task
- App lives under `task_ai_ml_02/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_2: ML experiment tracking (MLflow-like)` and start the next task immediately.

---

## Task 03 — Automated resume screening system
**workdir:** `task_ai_ml_03`
**id:** `ai_ml_03_automated-resume-screening-system`
**source:** `archive:python_15`
**dimensions:** complexity=low, value=medium, language_runtime=typescript, artifact_type=web_fullstack, task_family=ml_inference_eval, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=multi_turn_repair, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Create an Automated Resume Screening System in Python that scores resumes against a job description using keyword/skill heuristics or a small local model, with a review queue UI.

### Done criteria for this task
- App lives under `task_ai_ml_03/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=browser_smoke, tools=mixed)

When done, print `DONE task_3: Automated resume screening system` and start the next task immediately.

---

## Task 04 — AI document assistant
**workdir:** `task_ai_ml_04`
**id:** `ai_ml_04_ai-document-assistant`
**source:** `archive:python_13`
**dimensions:** complexity=hard, value=hard, language_runtime=python, artifact_type=web_fullstack, task_family=ml_inference_eval, agent_topology=single_agent, verification_mode=visual_diff, session_shape=approval_gated, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Build an AI Document Assistant: upload text/PDF, chunk and index locally, answer questions with citations from retrieved chunks (stub LLM OK if labeled).

### Done criteria for this task
- App lives under `task_ai_ml_04/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=visual_diff, tools=edit_heavy)

When done, print `DONE task_4: AI document assistant` and start the next task immediately.

---

## Task 05 — Sentiment triage inbox
**workdir:** `task_ai_ml_05`
**id:** `ai_ml_05_sentiment-triage-inbox`
**source:** `original`
**dimensions:** complexity=medium, value=low, language_runtime=javascript, artifact_type=backend_api, task_family=ml_inference_eval, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=single_shot, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Create a support inbox that classifies message sentiment/urgency with a small local model or lexicon baseline and routes tickets to queues.

### Done criteria for this task
- App lives under `task_ai_ml_05/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_5: Sentiment triage inbox` and start the next task immediately.

---

## Task 06 — Tabular churn predictor demo
**workdir:** `task_ai_ml_06`
**id:** `ai_ml_06_tabular-churn-predictor-demo`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=python, artifact_type=notebook_analysis, task_family=data_wrangling, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=multi_turn_repair, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=empty_scratch

### User request

Build a churn prediction demo: upload CSV, train a simple sklearn model, show feature importances, and predict on new rows.

### Done criteria for this task
- App lives under `task_ai_ml_06/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_6: Tabular churn predictor demo` and start the next task immediately.

---

## Task 07 — Embedding search for FAQs
**workdir:** `task_ai_ml_07`
**id:** `ai_ml_07_embedding-search-for-faqs`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=go, artifact_type=backend_api, task_family=ml_inference_eval, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=resume_mid_task, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Create an FAQ semantic search API using local embeddings (or TF-IDF fallback), with admin CRUD for FAQ entries and ranked answers.

### Done criteria for this task
- App lives under `task_ai_ml_07/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=browser_smoke, tools=mixed)

When done, print `DONE task_7: Embedding search for FAQs` and start the next task immediately.

---

## Task 08 — OCR receipt field extractor
**workdir:** `task_ai_ml_08`
**id:** `ai_ml_08_ocr-receipt-field-extractor`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=python, artifact_type=web_fullstack, task_family=ml_inference_eval, agent_topology=single_agent, verification_mode=static_pass, session_shape=multi_turn_repair, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Build a receipt field extractor: accept images, stub OCR to text if needed, parse merchant/date/total with rules, and return structured JSON + UI review.

### Done criteria for this task
- App lives under `task_ai_ml_08/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_8: OCR receipt field extractor` and start the next task immediately.

---

## Task 09 — Toxicity filter microservice
**workdir:** `task_ai_ml_09`
**id:** `ai_ml_09_toxicity-filter-microservice`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=rust, artifact_type=backend_api, task_family=ml_inference_eval, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=approval_gated, tool_profile=mixed, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Implement a toxicity/profanity filter microservice with batch and streaming endpoints, allowlists, and unit tests on fixtures.

### Done criteria for this task
- App lives under `task_ai_ml_09/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=mixed)

When done, print `DONE task_9: Toxicity filter microservice` and start the next task immediately.

---

## Task 10 — Time-series anomaly flagger
**workdir:** `task_ai_ml_10`
**id:** `ai_ml_10_time-series-anomaly-flagger`
**source:** `original`
**dimensions:** complexity=low, value=low, language_runtime=python, artifact_type=cli_tool, task_family=data_visualization, agent_topology=single_agent, verification_mode=static_pass, session_shape=single_shot, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a time-series anomaly flagger: ingest metric CSV, detect spikes with z-score/IQR, plot anomalies, and export flagged windows.

### Done criteria for this task
- App lives under `task_ai_ml_10/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_10: Time-series anomaly flagger` and start the next task immediately.

---

## After all 10 (ai_ml)

Print a final summary table: task id | path | stack | complexity | how to run.
Then stop.
