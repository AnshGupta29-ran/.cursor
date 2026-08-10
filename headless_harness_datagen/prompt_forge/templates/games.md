# Category template: Games / Interactive Simulations

Family shape for playable games and interactive sims with loops, scoring, and
progression. The deliverable must be playable — not a static screenshot UI.

## Product family intent

A player enters a session, interacts under clear rules, receives feedback (score,
health, resources), and progresses through difficulty or levels. Optional AI/opponent
modes must be real algorithms or behaviors, not random thrashing labeled “AI”.

## Identity & positioning (invent uniquely)

- Game premise and fantasy (defend outpost, grow colony, stealth courier, puzzle dojo)
- Session model (endless, waves, levels, campaign short)
- Victory/defeat conditions
- One twist (replay ghosts, daily seed, build-loadout, fog of war lite, assist mode)

## Required capability areas

### Core loop
- Input → world update → render feedback at interactive framerate for the stack
- Pause/resume if appropriate
- Deterministic rules documented

### Progression
- Score/resources
- Difficulty scaling or waves/levels
- Unlocks/upgrades if relevant (define economy)

### Entities & behaviors
- Player-controlled entity/tools
- NPC/enemy/obstacle behaviors with distinct classes if combat/sim
- Collision/path rules stated

### Meta systems
- Save/load or run history
- Settings (difficulty, speed, audio mute)
- Main menu / HUD polish beyond debug rectangles when stack allows

### AI mode (when seed asks)
- Named algorithm or behavior tree summary
- Visual debug optional (path overlay) if it helps verification

## UX expectations

- Immediate understandability of controls (overlay or README)
- Readable HUD
- Game-over / win screens with restart
- Performance acceptable on modest hardware for demo scope

## Data & persistence

Prefer local save files or lightweight DB for settings/high scores.
Content/config (levels, waves) in data files when possible.

## Quality & reliability

- Unit tests for pure logic (scoring, pathfinding, wave spawn) where separable
- Avoid flaky GUI tests; logic tests preferred
- Seeded randomness if reproducibility matters

## Documentation & deliverables

- README: controls, win conditions, how to run
- Design notes for loop and AI
- Known limitations

## Constraints & non-goals

- Source-first deliverable: C# scripts, levels, docs, and EditMode tests
- Do NOT require installing Unity Hub/Editor mid-run; if Unity is missing, still
  deliver a complete source tree plus a simple browser/canvas fallback prototype
- Not a full multiplayer live-service game unless the seed demands it

- Not a multiplayer netcode project unless seed is collaborative/realtime game
- Not AAA assets; simple primitives OK if cohesive
- Avoid non-interactive “game” that only prints text unless seed is CLI game

## Acceptance criteria checklist (customize)

- [ ] Game launches into a playable session
- [ ] Core loop runs with clear scoring/progress
- [ ] Defeat/victory paths work
- [ ] Save/settings work if specified
- [ ] AI/opponent mode works if specified and is non-trivial
- [ ] Logic tests cover at least one rules module
- [ ] README enables a first play session

## Variation axes

Genre · AI depth · meta progression · juice/juice-light · config-driven levels ·
accessibility assists

## Anti-clone rules

Do not regenerate the same snake/tower-defense paragraph blocks. Change fantasy,
systems mix, and win conditions for diversity.
