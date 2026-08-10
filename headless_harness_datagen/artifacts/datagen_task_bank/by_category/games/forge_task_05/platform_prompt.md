# Project Request / Product identity

**Product Name**: "Frostborne Clash"

**Domain twist**: A strategic card battler set in a frozen frontier where players control frost-wrought warriors, ice constructs, and snow elemental units. The game features a unique "Mana Crystallization" mechanic that allows players to convert excess mana into temporary buffs, and a "Frostline" timer that builds tension by limiting each turn to a fixed window.

**Primary fantasy**: Players are leaders of a mercenary faction fighting for survival in the Frozen Wastes, where every battle is fought under a shrinking glacier that slowly encroaches on the battlefield. Victory requires not just tactical skill but also managing time pressure and environmental hazards.

**Gameplay model**: Turn-based strategy with deck-building and resource management. Each player has a hand of 5 cards, starts with 3 mana, and gains 1 additional mana per turn up to a maximum of 10. A unique "Glacial Pulse" system dynamically adjusts difficulty based on the player's mana efficiency.

## Target users & primary jobs-to-be-done

**Target audience**: Strategy gamers aged 25-40 who enjoy games like Hearthstone, Dominion, and Slay the Spire but want something with more thematic immersion.

**Jobs-to-be-done**:
1. Build an optimal deck for my playstyle and current meta
2. Win matches against AI opponents using strategic card placement
3. Manage resources efficiently to maximize card value within time constraints
4. Learn from each match through visual feedback and score progression

## Core requirements / entities

### Entities

- **Player Character**: Controlled by user, has health, mana, deck, and hand
- **AI Opponent**: Simulated player with strategy trees for card selection and play
- **Card Types**: Creature (attack/health), Spell (instant effect), Artifact (permanent buff)
- **Mana System**: Crystal-based mana pool with crystallization mechanics
- **Battlefield**: 6x6 grid space for creature deployment and movement
- **Glacial Pulse Timer**: Countdown clock that affects combat timing and difficulty scaling
- **Frostline**: Environmental hazard that advances each turn, reducing available battlefield space

### Core Loop Requirements

- Input: Card selection, battlefield placement, ability activation
- World Update: Damage calculation, card draw, timer progression
- Feedback: Visual combat effects, score updates, UI alerts for critical events
- Deterministic behavior: Same inputs should always produce same outcomes for reproducibility

## Major feature areas

- **Deck Construction**: Build and modify decks from card collection (30 cards minimum, 100+ total unique cards)
- **Turn Management**: 30-second turn timer, mana regeneration, hand size management
- **Combat Mechanics**: Grid-based movement, attack targeting, spell effects, creature blocking
- **Frostline Mechanics**: Battlefield shrinkage that increases pressure as game progresses
- **Mana Crystallization**: Convert unused mana into temporary buffs or special actions
- **Difficulty Scaling**: Glacial Pulse system adapts AI strength based on player performance

## Domain-specific workflows

### Happy path gameplay:

1. Player opens game → main menu loads → selects "New Game"
2. Deck builder opens → player selects pre-made starter deck or customizes their own
3. Game begins → first turn starts with 3 mana → player draws cards
4. Player plays cards strategically → manages mana and battlefield position
5. AI opponent takes turn → player gets time-limited counter-response
6. Round ends → next round starts → glacial pulse increases difficulty slightly
7. Player wins when opponent's health reaches zero before time expires

### Edge cases:

- Out-of-mana scenarios (must skip turns if no playable cards)
- Battlefield full (cannot place creatures)
- Time expiration (player loses turn if no action taken)
- Exhausted abilities (cannot use same spell twice per turn)

## Data & persistence expectations

- Save file stores: high scores, unlocked cards, preferred decks, settings
- Local data storage via JSON files (not database required)
- Card database stored in structured config files for easy expansion
- Settings saved separately: audio volume, display preferences, difficulty level
- Game state includes: current hand, battlefield state, player stats, opponent stats

## UX / API surface expectations

- Clean HUD showing: health, mana, remaining time, frostline status
- Intuitive card drag-and-drop placement interface
- Visual feedback for all actions (damage effects, mana gain, spell impacts)
- Clear control instructions in main menu and during gameplay
- Turn timer display with warning color changes
- Victory/defeat screens with restart option and performance metrics

## Quality, security, and reliability expectations

- All game logic must be deterministic for scoring consistency
- No external dependencies beyond standard libraries for core functionality
- Logic tests for key systems (combat resolution, mana mechanics, AI decision trees)
- Performance must maintain stable frame rate at 60fps on modest hardware
- No network connectivity required; offline-first design
- Input validation to prevent invalid moves or cheating

## Documentation & testing expectations

- README explaining controls, win conditions, how to run the game
- Design notes detailing core loop, AI behavior, and progression system
- Unit tests covering: combat resolution logic, mana calculation, AI decision making
- Smoke test ensuring core gameplay functions work (draw cards, play creature, take damage)
- Test coverage of edge cases (out-of-mana scenarios, empty battlefield)

## Constraints & non-goals

- Source-first deliverable: C# scripts, levels, docs, and EditMode tests
- Do NOT require installing Unity Hub/Editor mid-run; deliver complete source tree plus canvas fallback prototype
- Not a multiplayer live-service game
- Not a full graphics-intensive AAA game; simple primitives acceptable
- Avoid static text-only UIs; must include interactive elements
- No asset bundles or external assets; rely only on standard engine primitives
- No complex networking or online features unless explicitly requested

## Acceptance criteria checklist

- [ ] Game launches into a playable session with intro screen
- [ ] Core loop runs with clear scoring/progress (win/loss conditions)
- [ ] Defeat/victory paths work consistently with clear end screens
- [ ] Save/settings work correctly and persist between sessions
- [ ] AI opponent makes meaningful decisions (not random card selection)
- [ ] Mana and Frostline mechanics function properly
- [ ] Logic tests cover at least one rules module (combat, mana, AI)
- [ ] README enables a first play session with clear instructions
- [ ] UI provides all necessary feedback without being cluttered
- [ ] Performance meets 60fps baseline on standard hardware

## Uniqueness / anti-clone constraints for this run

- Not another generic card battler or clone of existing popular games
- Must feature unique "Frostline" environmental mechanic that changes the game
- Requires proper implementation of Mana Crystallization system as a distinct game feature
- Must have deterministic game state for fair competition and scoring
- Must include a true turn-based AI with strategic depth beyond simple random play
- No snake/tower-defense/placeholder-style mechanics allowed
- Must implement a functional deck construction system with meaningful choices
- Requires a complete game loop with victory conditions and replayability
- Must have clean separation of gameplay logic from presentation layer
- Give final result without stopping with runnable desktop gameplay