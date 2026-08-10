# Typing race multiplayer local

- category: `games`
- source: `original`
- dimensions_hint: `{"agent_topology": "subagent_spawns", "verification_mode": "runtime_pass", "session_shape": "multi_turn_repair", "repo_state": "empty_scratch", "tool_profile": "edit_heavy", "user_persona": "solo_dev", "complexity": "low", "value": "medium", "language_runtime": "javascript", "artifact_type": "game_prototype", "task_family": "coding_implement", "business_domain": "education"}`

## Seed

Create a local multiplayer typing race: shared prompt, per-player progress bars, WPM, and winner screen.

## Run (single category pipeline)

```bash
python main.py "Create a local multiplayer typing race: shared prompt, per-player progress bars, WPM, and winner screen." --forge-prompt --forge-category games --workdir task_games_07
```
