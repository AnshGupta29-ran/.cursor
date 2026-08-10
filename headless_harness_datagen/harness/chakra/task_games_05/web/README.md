# Frostborne Clash (Task 05) — browser playable

Chakra generated a Unity scaffold under `../FrostborneClash/` (needs Unity Editor).
This folder is a **runnable HTML canvas** version you can open now.

## Run (browser)

```powershell
cd C:\Users\anshg\.cursor\headless_harness_datagen\harness\chakra\task_games_05\web
python -m http.server 8765
```

Open **http://127.0.0.1:8765/**

## Controls
- Click a **hand card**, then a **board cell** (creatures go on your bottom rows)
- Spells/artifacts cast on click
- **Crystallize** — spend remaining mana for +1 ATK buff
- **End Turn** — your creatures attack, then AI plays
- Frostline shrinks usable columns over time
