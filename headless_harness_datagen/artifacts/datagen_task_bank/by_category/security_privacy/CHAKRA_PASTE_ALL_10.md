# Category batch: security_privacy (all 10) — paste into Chakra

You are running a **datagen category marathon** for harness evaluation.
Category focus: **security/privacy — auth, crypto, or privacy-preserving demos**.

## Non-negotiable rules

1. Complete the **10 tasks below in order** (01 → 10). Do not skip.
2. Each task is a **separate app/project** under its own folder `task_security_privacy_NN/` (use the workdir listed).
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

Tag every DONE note with category `security_privacy` so logs are easy to grep.

---

## Task 01 — Secure password manager
**workdir:** `task_security_privacy_01`
**id:** `security_privacy_01_secure-password-manager`
**source:** `archive:6`
**dimensions:** complexity=low, value=medium, language_runtime=python, artifact_type=desktop_app, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=multi_turn_repair, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Create a desktop password manager using Python and PySide6 (Qt). Users should be able to create encrypted password vaults protected by a master password. Implement AES encryption, password generation, categories, search, clipboard copying with automatic clearing, password strength indicators, and secure import/export functionality. Include proper exception handling and unit tests for the encryption logic.

### Done criteria for this task
- App lives under `task_security_privacy_01/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=browser_smoke, tools=mixed)

When done, print `DONE task_1: Secure password manager` and start the next task immediately.

---

## Task 02 — Secrets vault API
**workdir:** `task_security_privacy_02`
**id:** `security_privacy_02_secrets-vault-api`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=typescript, artifact_type=backend_api, task_family=security_audit, agent_topology=single_agent, verification_mode=visual_diff, session_shape=approval_gated, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Build a secrets vault HTTP API: store sealed secrets, role-based read, audit log, and rotation metadata (no plaintext at rest).

### Done criteria for this task
- App lives under `task_security_privacy_02/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=visual_diff, tools=edit_heavy)

When done, print `DONE task_2: Secrets vault API` and start the next task immediately.

---

## Task 03 — 2FA login playground
**workdir:** `task_security_privacy_03`
**id:** `security_privacy_03_2fa-login-playground`
**source:** `original`
**dimensions:** complexity=medium, value=low, language_runtime=javascript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=single_shot, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Create an auth playground with password login, TOTP 2FA enrollment, backup codes, and session management.

### Done criteria for this task
- App lives under `task_security_privacy_03/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_3: 2FA login playground` and start the next task immediately.

---

## Task 04 — PII redaction CLI
**workdir:** `task_security_privacy_04`
**id:** `security_privacy_04_pii-redaction-cli`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=csharp, artifact_type=cli_tool, task_family=security_audit, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=multi_turn_repair, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=empty_scratch

### User request

Implement a PII redaction CLI that scans text/CSV for emails/phones/SSNs and writes redacted copies with a report.

### Done criteria for this task
- App lives under `task_security_privacy_04/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_4: PII redaction CLI` and start the next task immediately.

---

## Task 05 — Permission policy tester
**workdir:** `task_security_privacy_05`
**id:** `security_privacy_05_permission-policy-tester`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=cpp, artifact_type=cli_tool, task_family=security_audit, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=resume_mid_task, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Build a RBAC/ABAC policy tester: define roles/permissions, evaluate access queries, and show allow/deny with reasons.

### Done criteria for this task
- App lives under `task_security_privacy_05/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=browser_smoke, tools=mixed)

When done, print `DONE task_5: Permission policy tester` and start the next task immediately.

---

## Task 06 — JWT key rotation lab
**workdir:** `task_security_privacy_06`
**id:** `security_privacy_06_jwt-key-rotation-lab`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=rust, artifact_type=backend_api, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=multi_turn_repair, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a JWT auth service demo with key rotation, JWKS endpoint, and middleware verification tests.

### Done criteria for this task
- App lives under `task_security_privacy_06/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_6: JWT key rotation lab` and start the next task immediately.

---

## Task 07 — Secure file shredder utility
**workdir:** `task_security_privacy_07`
**id:** `security_privacy_07_secure-file-shredder-utility`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=go, artifact_type=cli_tool, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=approval_gated, tool_profile=mixed, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Build a secure delete utility that overwrites files before unlink and logs operations (cross-platform best-effort).

### Done criteria for this task
- App lives under `task_security_privacy_07/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=mixed)

When done, print `DONE task_7: Secure file shredder utility` and start the next task immediately.

---

## Task 08 — Consent and cookie preference center
**workdir:** `task_security_privacy_08`
**id:** `security_privacy_08_consent-and-cookie-preference-center`
**source:** `original`
**dimensions:** complexity=low, value=low, language_runtime=java, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=single_shot, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a consent preference center UI + API: categories of tracking, versioned policies, and user consent records.

### Done criteria for this task
- App lives under `task_security_privacy_08/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_8: Consent and cookie preference center` and start the next task immediately.

---

## Task 09 — API abuse rate-limit gateway
**workdir:** `task_security_privacy_09`
**id:** `security_privacy_09_api-abuse-rate-limit-gateway`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=typescript, artifact_type=backend_api, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=multi_turn_repair, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=empty_scratch

### User request

Build a rate-limit gateway middleware/service with token buckets per API key, 429 responses, and metrics.

### Done criteria for this task
- App lives under `task_security_privacy_09/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_9: API abuse rate-limit gateway` and start the next task immediately.

---

## Task 10 — Certificate expiry monitor
**workdir:** `task_security_privacy_10`
**id:** `security_privacy_10_certificate-expiry-monitor`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=python, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=resume_mid_task, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=partial_scaffold

### User request

Create a TLS certificate expiry monitor: check hosts, store notAfter dates, alert when within N days, simple dashboard.

### Done criteria for this task
- App lives under `task_security_privacy_10/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_10: Certificate expiry monitor` and start the next task immediately.

---

## After all 10 (security_privacy)

Print a final summary table: task id | path | stack | complexity | how to run.
Then stop.
