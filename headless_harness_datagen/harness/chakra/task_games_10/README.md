# SeedStreet Exchange (Task 10)

Deterministic Meridian Archipelago paper-trading arena. Same seed → same storm.

## Run (Python — no Go required)

```powershell
cd headless_harness_datagen/harness/chakra/task_games_10
python seedstreet.py --seed 7 --port 8080
```

Open: http://127.0.0.1:8080/

Snapshot mode (stable HTML for visual-diff):

```powershell
python seedstreet.py --seed 7 --port 8080 --snapshot
```

## Smoke

```powershell
python smoke.py
```

## Rules
- Starting cash: 10,000 credits
- Long-only, whole shares, fee 0.15% (min 1 credit)
- Market day = ticks 0–239; advancing past 239 force-settles
- Prices are a pure function of `(seed, symbol, tick)` via SplitMix64

## Routes
- `GET /` — desk + new run
- `POST /run/new` — create run
- `GET /run/{id}` — trading floor
- `POST /run/{id}/trade|advance|settle`
- `GET /run/{id}/tape`
- `GET /leaderboard?seed=`

## Note
Incomplete Go stubs remain in this folder from an earlier attempt; **use `seedstreet.py`** to play.
