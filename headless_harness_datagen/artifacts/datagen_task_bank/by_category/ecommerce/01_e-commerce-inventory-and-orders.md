# E-commerce inventory and orders

- category: `ecommerce`
- source: `archive:7`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "typescript", "artifact_type": "web_fullstack", "task_family": "coding_implement", "business_domain": "ecommerce"}`

## Seed

Create a full-stack inventory management system using React, Node.js, Express, PostgreSQL, and Prisma. Administrators should be able to manage products, categories, suppliers, inventory levels, purchase orders, and customer orders. Include dashboards with analytics, low-stock alerts, pagination, filtering, authentication, and REST APIs with proper validation. Write automated backend tests for critical endpoints.

## Run (single category pipeline)

```bash
python main.py "Create a full-stack inventory management system using React, Node.js, Express, PostgreSQL, and Prisma. Administrators should be able to manage products, categories, suppliers, inventory levels, purchase orders, and customer orders. Include dashboards with analytics, low-stock alerts, pagination, filtering, authentication, and REST APIs with proper validation. Write automated backend tests for critical endpoints." --forge-prompt --forge-category ecommerce --workdir task_ecommerce_01
```
