# MeritLens

Auditable, rubric-driven resume screening for **apprenticeship / skilled-trades cohort hiring** (union training centers, community-college workforce boards). Every score decomposes into named weighted criteria (OSHA-30, NCCER, PLC basics, etc.) — not an opaque AI match %.

## Install & run (browser)

```bash
cd meritlens
npm install
npm run dev
```

Open http://127.0.0.1:5173/ — seeded **Industrial Maintenance Apprentice** profile + 3 fixture resumes, scored and auto-bucketed (unconfirmed until you press `a`/`h`/`r`).

Desktop shell (optional):

```bash
npm run desktop
```

## CLI

```bash
npm run screen -- --profile fixtures/profile.json --resumes fixtures/resumes
npm run screen -- --profile fixtures/profile.json --resumes fixtures/resumes --json --out results.json
```

## Sample walkthrough

1. Queue shows Rivera / Okonkwo / Chen with rubric scores.
2. Press `j`/`k` to move, `Enter` for detail (evidence highlights).
3. Confirm buckets with `a` (advance), `h` (hold), `r` (reject) — aria-live announces.
4. Roles tab: change thresholds or presets (`strict` / `open-cohort`) — queue re-buckets; audit log updated.
5. Export JSON/CSV or full workspace.

## Keyboard map

| Key | Action |
|-----|--------|
| `j` / `k` or arrows | Move queue selection |
| `Enter` | Open candidate detail |
| `a` / `h` / `r` | Advance / Hold / Reject |
| `e` | Export decisions JSON |
| `1` / `2` / `3` | Queue / Detail / Roles |
| `?` | Shortcut overlay |
| `Esc` | Close overlay |

## Tests & smoke

```bash
npm test
npm run smoke
```

Smoke builds the app, checks `dist`, runs CLI screen, and exercises a jsdom `j`/`a` triage path when `jsdom` is installed (otherwise static+CLI mode — still PASS).

## Limitations

- English-only keyword / synonym heuristics — not legal or defensibility advice.
- Synonym lists bias who matches; missing synonyms under-score good candidates.
- No PDF/DOCX parsing; `.txt` / `.md` only; max 200 KB.
- No external ML APIs. A real embedding/LLM judge could replace `scoreResume` later while keeping the same breakdown UI and audit trail.

## Persistence

Browser state lives in `localStorage` key `meritlens.v1`. Export/import workspace JSON for round-trips. CLI is stateless.
