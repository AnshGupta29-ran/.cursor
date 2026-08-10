# Minesweeper with Difficulty Presets and Hint Mode

## Project Request / Product identity

A deterministic, logic-based puzzle game where players clear a grid of mines using deductive reasoning. The game offers three difficulty presets (Beginner: 8x8 with 10 mines, Intermediate: 16x16 with 40 mines, Expert: 30x16 with 99 mines) and includes an intelligent hint system that highlights safe squares based on logical deduction.

## Target users & primary jobs-to-be-done

Target users are puzzle enthusiasts, logic problem solvers, and casual gamers who enjoy strategy games requiring pattern recognition and careful analysis. Primary jobs-to-be-done include:
- Clearing all non-mine squares to win
- Solving puzzles without making incorrect guesses
- Learning optimal strategies through guided hints
- Comparing performance across difficulty levels

## Core requirements / entities

### Entities
- Grid board (8x8, 16x16, or 30x16 depending on difficulty)
- Mine tiles (hidden, flagged, exploded)
- Numbered clue tiles (1-8)
- Player cursor/selection
- Game state (playing, won, lost)
- Difficulty settings (Beginner, Intermediate, Expert)
- Hint mode toggle

### Capabilities
- Click to reveal tiles with immediate visual feedback
- Right-click to flag suspected mine locations
- Game state transitions (win/lose detection)
- Hint algorithm for logical deductions
- Difficulty-prescribed mine placement
- Session persistence for settings and high scores

## Major feature areas

### Core gameplay loop
- Tile interaction with reveal/flag mechanics
- Immediate visual feedback for tile actions
- Win condition (all non-mine tiles revealed)
- Lose condition (mine clicked)
- Progressive difficulty scaling

### Hint system
- Intelligent deduction engine that identifies safe squares
- Visual highlight overlay for suggested moves
- Hint availability tracking (limited per game session)
- Non-intrusive UI indicator when hint available

### Progression systems
- High score tracking per difficulty level
- Time-based performance metrics
- Hint usage statistics
- Win/loss ratio by difficulty

### Settings & UI
- Difficulty preset selection menu
- Hint mode toggle switch
- Timer display
- Mine counter
- Reset/restart button
- Main menu with game info

## Domain-specific workflows

### Happy path
1. User selects difficulty preset
2. Game generates valid minefield with proper mine count
3. Player clicks tiles to reveal numbers/clues
4. Player flags suspected mines with right-click
5. Game automatically reveals adjacent safe tiles
6. Player deduces remaining safe tiles via logical process
7. All non-mine tiles revealed → win screen
8. Player can restart or change difficulty

### Edge cases
- First click never lands on mine (reposition if needed)
- Clicking a numbered tile reveals adjacent unflagged tiles
- Game over when any mine is clicked
- Hint mode only shows one suggestion at a time
- Hint exhaustion after 5 uses per game session
- Time tracking only during active play sessions
- Difficulty changes reset current game state

## Data & persistence expectations

### Persistent data
- High scores per difficulty level (best times)
- Hint usage statistics
- Last selected difficulty
- Game settings (hint mode enabled/disabled)

### Local storage
- Save file for settings and high scores in JSON format
- Optional session data for game state restoration (if implemented)
- Configuration files for board dimensions and mine counts

### Content
- Predefined board sizes and mine counts for each difficulty
- Logical deduction rules defined as code constants
- Hint algorithm decision trees stored in class methods

## UX / API surface expectations

### Controls
- Left-click: Reveal tile
- Right-click: Flag/Unflag tile
- Spacebar: Toggle hint mode
- R key: Restart current game
- Esc key: Return to main menu

### Interface elements
- Grid-based board with numbered clues
- Numeric display for remaining mine count
- Timer showing elapsed seconds
- Status bar indicating game state
- Hint indicator (lightbulb icon)
- Difficulty selector dropdown

### Visual feedback
- Tile reveal animation
- Flag placement animation
- Mine explosion effect on loss
- Highlighted safe tile when hint activated
- Clear status indicators for win/lose states

## Quality, security, and reliability expectations

### Code quality
- Clean separation between game logic and rendering
- Unit tests for core game rules (reveal logic, win conditions)
- Consistent coordinate handling (row/column indexing)
- Deterministic behavior for reproducible games

### Reliability
- No random failures in game state calculations
- Proper mine placement algorithm that avoids initial mine clicks
- Stable hint algorithm with predictable behavior
- Graceful handling of edge cases (first-click safety, hint exhaustion)

### Performance
- Fast tile reveal operations
- Efficient hint calculation algorithms
- Responsive input handling
- Minimal memory footprint

## Documentation & testing expectations

### README content
- Controls reference
- How to play instructions
- Difficulty level details
- Hint system explanation
- Building and running instructions
- Known limitations

### Design documentation
- Game rules specification
- Hint algorithm description
- Board generation process
- Difficulty presets configuration

### Testing approach
- Logic tests for tile reveal rules
- Win/lose condition validation
- Hint algorithm correctness verification
- Difficulty level consistency checks
- First-click safety verification

## Constraints & non-goals

### Platform constraints
- Single-player experience only
- No network multiplayer features
- No sound effects or complex animations
- Lightweight implementation suitable for low-end hardware
- No external dependencies beyond standard libraries

### Non-goals
- Multiplayer real-time game functionality
- Advanced AI opponents
- High-fidelity graphics or complex UI
- Cloud save synchronization
- Persistent leaderboards
- Advanced hint explanations or tutorials

## Acceptance criteria (checkable)

- [ ] Game launches into playable main menu
- [ ] All three difficulty presets function correctly with appropriate board sizes and mine counts
- [ ] First click never results in a mine location
- [ ] Standard tile reveal mechanics work properly
- [ ] Flagging/unflagging functionality works with proper visual indicators
- [ ] Win condition triggers when all non-mine tiles are revealed
- [ ] Loss condition triggers when mine is clicked
- [ ] Hint system correctly identifies and highlights safe tiles based on logical deduction
- [ ] Hint mode toggles properly and shows available hints
- [ ] High score tracking works for all difficulty levels
- [ ] Settings persist between sessions
- [ ] Game provides clear visual feedback for all interactions
- [ ] README contains complete controls and gameplay instructions
- [ ] Unit tests cover core game rules and hint algorithms

## Uniqueness / anti-clone constraints for this run

- Must implement intelligent hint mode that performs logical deduction rather than random tile selection
- Each difficulty preset must have truly distinct board sizes and mine counts, not arbitrary variations
- First-click safety must be guaranteed through actual mine repositioning algorithm, not luck
- Hint system must be mathematically sound and provide only safe deductions
- Not just another "click tiles to reveal" game - must emphasize logical reasoning and strategy
- Cannot be a simple reimplementation of classic Minesweeper with cosmetic changes
- Must include proper win/lose detection with visual feedback
- Gameplay must be fully deterministic with no randomness in tile reveal or mine placement except for initial setup