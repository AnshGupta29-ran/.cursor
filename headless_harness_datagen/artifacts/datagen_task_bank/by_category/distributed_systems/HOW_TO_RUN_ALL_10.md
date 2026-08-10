# Run all 10 `distributed_systems` tasks in one Chakra session

## 1. Start Chakra

```powershell
cd C:\Users\anshg\.cursor\headless_harness_datagen\harness\chakra
chakra --dangerously-skip-permissions
```

Optional model:

```powershell
chakra --model kimi3 --dangerously-skip-permissions
```

## 2. Paste the batch file

Open and paste the **entire** contents of:

`artifacts/datagen_task_bank/by_category/distributed_systems/CHAKRA_PASTE_ALL_10.md`

into the Chakra prompt. Press Enter once.

Chakra will work through tasks 01–10 sequentially until each is demoable.

## 3. Stats website (auto on hard refresh)

Start once (can stay running while Chakra works):

```powershell
cd C:\Users\anshg\.cursor\headless_harness_datagen
python -m prompt_stats serve
```

Open **http://127.0.0.1:8787/**. Hard-refresh the browser whenever you want latest
session time/tokens — the page runs a full collect on load. No separate `collect` step.

## 4. One-at-a-time (pipeline / forge)

```powershell
cd C:\Users\anshg\.cursor\headless_harness_datagen
python scripts/run_task_bank_category.py distributed_systems
```

## 5. Dimension coverage

Each of the 10 tasks targets a different mix of:

- complexity / value (low | medium | hard)
- agent_topology, verification_mode, session_shape
- tool_profile, user_persona, repo_state
- language_runtime, artifact_type, task_family

So the harness sees **variety**, not 10 copies of the same shape.
