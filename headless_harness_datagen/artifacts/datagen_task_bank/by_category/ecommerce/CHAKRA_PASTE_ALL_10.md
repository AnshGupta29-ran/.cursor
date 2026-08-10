# Category batch: ecommerce (all 10) — paste into Chakra

You are running a **datagen category marathon** for harness evaluation.
Category focus: **ecommerce — catalog/cart/checkout browser flows**.

## Non-negotiable rules

1. Complete the **10 tasks below in order** (01 → 10). Do not skip.
2. Each task is a **separate app/project** under its own folder `task_ecommerce_NN/` (use the workdir listed).
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

Tag every DONE note with category `ecommerce` so logs are easy to grep.

---

## Task 01 — E-commerce inventory and orders
**workdir:** `task_ecommerce_01`
**id:** `ecommerce_01_e-commerce-inventory-and-orders`
**source:** `archive:7`
**dimensions:** complexity=medium, value=medium, language_runtime=typescript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=multi_turn_repair, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=empty_scratch

### User request

Create a full-stack inventory management system using React, Node.js, Express, PostgreSQL, and Prisma. Administrators should be able to manage products, categories, suppliers, inventory levels, purchase orders, and customer orders. Include dashboards with analytics, low-stock alerts, pagination, filtering, authentication, and REST APIs with proper validation. Write automated backend tests for critical endpoints.

### Done criteria for this task
- App lives under `task_ecommerce_01/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_1: E-commerce inventory and orders` and start the next task immediately.

---

## Task 02 — Restaurant ordering system
**workdir:** `task_ecommerce_02`
**id:** `ecommerce_02_restaurant-ordering-system`
**source:** `archive:python_5`
**dimensions:** complexity=hard, value=hard, language_runtime=python, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=resume_mid_task, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=partial_scaffold

### User request

Create a Restaurant Ordering System in Python: menu, cart, order statuses, kitchen view, and basic payments stub.

### Done criteria for this task
- App lives under `task_ecommerce_02/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_2: Restaurant ordering system` and start the next task immediately.

---

## Task 03 — Inventory management system
**workdir:** `task_ecommerce_03`
**id:** `ecommerce_03_inventory-management-system`
**source:** `archive:python_10`
**dimensions:** complexity=low, value=medium, language_runtime=javascript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=multi_turn_repair, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Create an Inventory Management System in Python for SKUs, stock adjustments, suppliers, and low-stock reports.

### Done criteria for this task
- App lives under `task_ecommerce_03/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=browser_smoke, tools=mixed)

When done, print `DONE task_3: Inventory management system` and start the next task immediately.

---

## Task 04 — Bike shop merchant catalog
**workdir:** `task_ecommerce_04`
**id:** `ecommerce_04_bike-shop-merchant-catalog`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=csharp, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=visual_diff, session_shape=approval_gated, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Build a bike shop merchant catalog with variants (size/color), inventory counts, and checkout cart (no payment processor required).

### Done criteria for this task
- App lives under `task_ecommerce_04/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=visual_diff, tools=edit_heavy)

When done, print `DONE task_4: Bike shop merchant catalog` and start the next task immediately.

---

## Task 05 — Subscription box admin
**workdir:** `task_ecommerce_05`
**id:** `ecommerce_05_subscription-box-admin`
**source:** `original`
**dimensions:** complexity=medium, value=low, language_runtime=java, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=subagent_spawns, verification_mode=unit_tests, session_shape=single_shot, tool_profile=shell_heavy, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Create a subscription-box admin: plans, subscriber list, skip/pause months, and fulfillment export CSV.

### Done criteria for this task
- App lives under `task_ecommerce_05/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=unit_tests, tools=shell_heavy)

When done, print `DONE task_5: Subscription box admin` and start the next task immediately.

---

## Task 06 — Marketplace listings for crafts
**workdir:** `task_ecommerce_06`
**id:** `ecommerce_06_marketplace-listings-for-crafts`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=typescript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=multi_turn_repair, tool_profile=browser_heavy, user_persona=pm_non_technical, repo_state=empty_scratch

### User request

Build a craft marketplace: seller listings, buyer search/filters, orders, and simple ratings.

### Done criteria for this task
- App lives under `task_ecommerce_06/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=browser_heavy)

When done, print `DONE task_6: Marketplace listings for crafts` and start the next task immediately.

---

## Task 07 — Coupon and promo engine
**workdir:** `task_ecommerce_07`
**id:** `ecommerce_07_coupon-and-promo-engine`
**source:** `original`
**dimensions:** complexity=medium, value=medium, language_runtime=go, artifact_type=backend_api, task_family=coding_implement, agent_topology=tool_swarm, verification_mode=browser_smoke, session_shape=resume_mid_task, tool_profile=mixed, user_persona=enterprise_buyer, repo_state=legacy_messy

### User request

Implement a coupon engine API: percent/fixed discounts, min cart, expiry, stacking rules, and unit tests.

### Done criteria for this task
- App lives under `task_ecommerce_07/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=medium, verification=browser_smoke, tools=mixed)

When done, print `DONE task_7: Coupon and promo engine` and start the next task immediately.

---

## Task 08 — Returns and RMA portal
**workdir:** `task_ecommerce_08`
**id:** `ecommerce_08_returns-and-rma-portal`
**source:** `original`
**dimensions:** complexity=low, value=medium, language_runtime=python, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=multi_turn_repair, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a returns/RMA portal: request return, reasons, approval workflow, and refund status tracking.

### Done criteria for this task
- App lives under `task_ecommerce_08/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_8: Returns and RMA portal` and start the next task immediately.

---

## Task 09 — Wholesale price list Excel sync
**workdir:** `task_ecommerce_09`
**id:** `ecommerce_09_wholesale-price-list-excel-sync`
**source:** `original`
**dimensions:** complexity=hard, value=hard, language_runtime=excel_office, artifact_type=spreadsheet_workbook, task_family=spreadsheet_excel, agent_topology=plan_then_execute, verification_mode=runtime_pass, session_shape=approval_gated, tool_profile=mixed, user_persona=staff_eng, repo_state=partial_scaffold

### User request

Build a wholesale price-list tool that imports/exports Excel price sheets and applies tier pricing to an in-app catalog.

### Done criteria for this task
- App lives under `task_ecommerce_09/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=hard, verification=runtime_pass, tools=mixed)

When done, print `DONE task_9: Wholesale price list Excel sync` and start the next task immediately.

---

## Task 10 — POS lite for cafe
**workdir:** `task_ecommerce_10`
**id:** `ecommerce_10_pos-lite-for-cafe`
**source:** `original`
**dimensions:** complexity=low, value=low, language_runtime=typescript, artifact_type=web_fullstack, task_family=coding_implement, agent_topology=single_agent, verification_mode=static_pass, session_shape=single_shot, tool_profile=edit_heavy, user_persona=solo_dev, repo_state=empty_scratch

### User request

Create a cafe POS lite: product buttons, ticket, tax, cash/card stub tender, and daily sales report.

### Done criteria for this task
- App lives under `task_ecommerce_10/`
- Runnable demo (browser / CLI / playable) without further questions
- Reflect dimensions above (esp. complexity=low, verification=static_pass, tools=edit_heavy)

When done, print `DONE task_10: POS lite for cafe` and start the next task immediately.

---

## After all 10 (ecommerce)

Print a final summary table: task id | path | stack | complexity | how to run.
Then stop.
