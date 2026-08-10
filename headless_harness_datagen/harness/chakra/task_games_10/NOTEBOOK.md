# NOTEBOOK — SeedStreet seed-7 walkthrough

1. Start server: `python seedstreet.py --seed 7 --port 8080`
2. Open http://127.0.0.1:8080/ — expect "SeedStreet Exchange" and "Meridian Archipelago".
3. Handle `Demo`, seed `7` → Ring the floor bell → redirected to `/run/{id}`.
4. Expect 5 instruments: KELP, BRINE, AMBR, SALTGLASS, CORAL with SVG charts.
5. Buy KELP qty 40 → cash decreases by qty×price+fee.
6. Advance 10 → tick becomes 10; a dispatch banner may appear if an event tick ≤ 10.
7. Sell KELP qty 20 → holdings drop.
8. Advance to close → status Settled; profit shown; leaderboard gains a row for seed 7.
9. Open tape — every trade lists tick/symbol/side/qty/price/fee.
10. Repeat steps 3–8 with identical actions on a second handle → identical profit (determinism).
