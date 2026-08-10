# Distributed task queue (Go)

- category: `distributed_systems`
- source: `archive:10`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "hard", "value": "hard", "language_runtime": "go", "artifact_type": "backend_api", "task_family": "coding_implement", "business_domain": "devops_platform"}`

## Seed

Create a distributed task queue framework using Go. Implement a central scheduler, multiple worker nodes, task prioritization, retries with exponential backoff, worker heartbeats, failure detection, persistent job storage using SQLite, and a REST API for submitting and monitoring jobs. Include structured logging, graceful shutdown, concurrency using goroutines, and automated integration tests demonstrating multiple workers processing jobs simultaneously.

## Run (single category pipeline)

```bash
python main.py "Create a distributed task queue framework using Go. Implement a central scheduler, multiple worker nodes, task prioritization, retries with exponential backoff, worker heartbeats, failure detection, persistent job storage using SQLite, and a REST API for submitting and monitoring jobs. Include structured logging, graceful shutdown, concurrency using goroutines, and automated integration tests demonstrating multiple workers processing jobs simultaneously." --forge-prompt --forge-category distributed_systems --workdir task_distributed_systems_01
```
