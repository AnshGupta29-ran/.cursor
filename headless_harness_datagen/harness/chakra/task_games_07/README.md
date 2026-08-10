# STATICLINE — Intercept Desk

A local-multiplayer typing race set in a 1970s **numbers-station listening post**. 2–4 operators are rival intercept operators transcribing the same burst transmission — but since there's only one keyboard, races run as **asynchronous ghost relays**: operators run one at a time while previously recorded opponents replay as live "ghost" progress lanes.

Built with **React + Vite + Vitest**. No backend, no netcode.

---

## The Fantasy

_Welcome to STATICLINE, an abandoned SIGINT relay station deep in the pine barrens. A burst transmission crackles through the static — coordinates, code phrases, situation reports from an unseen war. Your job: transcribe it before the signal fades. But you're not alone on this frequency. Other operators are listening too, and the Watchtower ranks every call sign by key rate and fidelity._

---

## Controls

| Key         | Action                            |
|-------------|-----------------------------------|
| Type        | Advance the transmission          |
| Backspace   | Correct the previous character    |
| Escape      | Forfeit the current run           |
| Tab / Click | Focus the input field             |

---

## How Ghost Relay Works

1. **Roster**: Set up 2–4 operators with unique call signs.
2. **Seeded transmission**: A transmission is deterministically chosen based on a seed. Same seed = same transmission every time.
3. **Round-robin relay**: Each operator types the transmission solo on the shared keyboard. The run is recorded as a timestamped keystroke log.
4. **Ghost replays**: When operator N types, operators 1 through N−1 replay as ghost lanes — live progress bars driven by their keystroke logs. The ghosts always move deterministically: same log + same elapsed time = same position.
5. **Scoring**: Finished runs are ranked by elapsed time. Unfinished runs (timeout/forfeit) rank below, sorted by progress then accuracy. Exact time ties are broken by accuracy, then WPM.
6. **Winner**: Top operator gets the call sign on the winner screen, with full per-run stats.

Ghost replay is **speed-adjustable** (0.5×, 1×, 2× in Settings) and always deterministic — a pure function of `(keystrokeLog, elapsedMs, speedMultiplier)`.

---

## Getting Started

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

Open `http://localhost:5173` in your browser. No Docker required.

---

## Project Structure

```
src/
├── main.jsx              # Entry point
├── App.jsx               # App root + view router
├── index.css             # Retro-terminal styles (phosphor green palette)
├── components/
│   ├── Menu.jsx          # Main menu
│   ├── Setup.jsx         # Operator roster + transmission config
│   ├── Countdown.jsx     # 3-2-1 countdown
│   ├── Race.jsx          # Core race loop with typing + ghost lanes
│   ├── Results.jsx       # Winner screen with ranked table
│   ├── History.jsx       # Last 10 matches from localStorage
│   ├── SettingsView.jsx  # Ghost speed, length class, time cap
│   └── DemoDesk.jsx      # Auto-play demo match with recorded data
├── lib/
│   ├── rng.js            # Seeded PRNG (mulberry32)
│   ├── scoring.js        # WPM, accuracy, progress math
│   ├── race.js           # Ranking / winner determination
│   ├── ghost.js          # Ghost position at time t
│   ├── storage.js        # Versioned localStorage persistence
│   ├── *.test.js         # Vitest unit tests for each module
└── data/
    ├── transmissions.js  # 12+ in-fiction intercept transmissions
    └── demoData.js       # Sample keystroke logs for Demo Desk
```

---

## Design Notes

### Scoring Formula
- **WPM** = (correctChars / 5) / (elapsedMinutes)
- **Accuracy** = correctKeystrokes / totalKeystrokes (backspace counts as keystroke)
- **Progress** = correctChars / totalChars

### Ghost Determinism
Ghost replay is a pure function: `ghostPositionAt(keystrokeLog, elapsedMs, speedMultiplier)`. This guarantees the same inputs always produce the same rendered position, making replays perfectly reproducible across page reloads and speed changes.

### Seeded RNG
Uses [mulberry32](https://gist.github.com/tommyettinger/46a874533244883189143505d203312c), a simple 32-bit PRNG, for deterministic transmission selection and shuffling. Same seed = same transmission every time, enabling reproducible matches and fair comparison.

### localStorage Schema
All data stored under versioned keys (`staticline:v1:*`). Schema version check on startup migrates or resets data if format changes. Matches capped at 10. Corrupted data falls back to defaults safely.

---

## Demoing

The **Demo Desk** (from the main menu) plays a complete 2-operator match using shipped sample keystroke logs with realistic WPM curves and injected typos. No keyboard input needed — just sit back and watch ghost lanes race.

---

## Known Limitations

- Single keyboard only — true simultaneous multiplayer would require netcode (out of scope).
- No sound effects in the current build (mute toggle is a placeholder).
- Demo desk runs the same sample match each time (seeded for consistency).

---

## License

MIT
