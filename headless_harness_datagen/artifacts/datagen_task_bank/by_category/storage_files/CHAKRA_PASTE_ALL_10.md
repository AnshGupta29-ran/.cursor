# Category batch: storage_files (all 10) — paste into Chakra

You are running a **datagen category marathon** for harness evaluation.
Category focus: **storage/files — upload, sync, or file-manager demos**.

## Non-negotiable rules

1. Complete the **10 tasks below in order** (01 → 10). Do not skip.
2. Each task is a **separate app/project** under its own folder `task_storage_files_NN/` (use the workdir listed).
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

Tag every DONE note with category `storage_files` so logs are easy to grep.

---

## Task 01 — Mini cloud storage platform
**workdir:** `task_storage_files_01`
**id:** `storage_files_01_mini-cloud-storage-platform`
**source:** `archive:2`
**dimensions:** complexity=medium, value=low, language_runtime=python, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=single_shot, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Create a cloud storage web application using React, Node.js, Express, and MongoDB. Users should be able to register, log in, upload files, organize them into folders, rename, move, delete, search, and download files. Implement JWT-based authentication, file size validation, storage usage statistics, and a clean dashboard.

### Done criteria for this task
- App lives under `task_storage_files_01/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_1: Mini cloud storage platform` and start the next task immediately.

---

## Task 02 — File sharing platform
**workdir:** `task_storage_files_02`
**id:** `storage_files_02_file-sharing-platform`
**source:** `archive:python_7`
**dimensions:** complexity=hard, value=hard, language_runtime=typescript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=multi_turn_repair, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=empty_scratch

### User request

Create a File Sharing Platform in Python: users upload files, get shareable links with optional expiry and password, track download counts, and manage their uploads via a simple web UI.

### Done criteria for this task
- App lives under `task_storage_files_02/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_2: File sharing platform` and start the next task immediately.

---

## Task 03 — Team document vault with preview
**workdir:** `task_storage_files_03`
**id:** `storage_files_03_team-document-vault-with-preview`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=javascript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=resume_mid_task, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Build a team document vault with folder ACLs, text/PDF preview, upload quotas per team, and audit logs of downloads.

### Done criteria for this task
- App lives under `task_storage_files_03/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=browser_smoke, tools=mixed)

When done, print `DONE task_3: Team document vault with preview` and start the next task immediately.

---

## Task 04 — Media library with tags
**workdir:** `task_storage_files_04`
**id:** `storage_files_04_media-library-with-tags`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=csharp, artifact_type=backend_api, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=multi_turn_repair, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a media library service for images and videos: upload, tag, search, thumbnail generation stubs, and collections.

### Done criteria for this task
- App lives under `task_storage_files_04/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_4: Media library with tags` and start the next task immediately.

---

## Task 05 — S3-like local object store CLI
**workdir:** `task_storage_files_05`
**id:** `storage_files_05_s3-like-local-object-store-cli`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=cpp, artifact_type=cli_tool, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=approval_gated, tool_profile=mixed, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Implement a local S3-like object store CLI and HTTP API: buckets, put/get/list/delete objects, and simple versioning.

### Done criteria for this task
- App lives under `task_storage_files_05/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=mixed)

When done, print `DONE task_5: S3-like local object store CLI` and start the next task immediately.

---

## Task 06 — Encrypted file dropbox
**workdir:** `task_storage_files_06`
**id:** `storage_files_06_encrypted-file-dropbox`
**source:** `original`
**dimensions:** complexity=low, value=low, language_runtime=rust, artifact_type=backend_api, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=single_shot, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Build an encrypted file drop service: client-side or server-side encryption, one-time download links, and expiry.

### Done criteria for this task
- App lives under `task_storage_files_06/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_6: Encrypted file dropbox` and start the next task immediately.

---

## Task 07 — Lab dataset repository
**workdir:** `task_storage_files_07`
**id:** `storage_files_07_lab-dataset-repository`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=go, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=multi_turn_repair, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=empty_scratch

### User request

Create a research dataset repository: upload zipped datasets, metadata forms, license tags, and download permissions by role.

### Done criteria for this task
- App lives under `task_storage_files_07/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_7: Lab dataset repository` and start the next task immediately.

---

## Task 08 — Receipt image archive
**workdir:** `task_storage_files_08`
**id:** `storage_files_08_receipt-image-archive`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=java, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=resume_mid_task, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=partial_scaffold

### User request

Build a receipt/image archive with folders by month, OCR-ready file naming, search by filename/tags, and bulk export.

### Done criteria for this task
- App lives under `task_storage_files_08/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_8: Receipt image archive` and start the next task immediately.

---

## Task 09 — CAD drawing document locker
**workdir:** `task_storage_files_09`
**id:** `storage_files_09_cad-drawing-document-locker`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=typescript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=multi_turn_repair, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Create a document locker for engineering drawings: check-in/check-out, revision numbers, and lock ownership.

### Done criteria for this task
- App lives under `task_storage_files_09/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=browser_smoke, tools=mixed)

When done, print `DONE task_9: CAD drawing document locker` and start the next task immediately.

---

## Task 10 — Excel workbook drop zone
**workdir:** `task_storage_files_10`
**id:** `storage_files_10_excel-workbook-drop-zone`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=python, artifact_type=spreadsheet_workbook, task_family=spreadsheet_excel, agent_topology=single_agent, verification_mode=visual_diff, session_shape=approval_gated, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Build a small service that accepts Excel/CSV uploads, validates sheets, stores them, and lists workbook metadata (sheet names, row counts) without requiring MS Office installed.

### Done criteria for this task
- App lives under `task_storage_files_10/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=visual_diff, tools=edit_heavy)

When done, print `DONE task_10: Excel workbook drop zone` and start the next task immediately.

---

## After all 10 (storage_files)

Print a final summary table: task id | path | stack | complexity | how to run.
Then stop.
