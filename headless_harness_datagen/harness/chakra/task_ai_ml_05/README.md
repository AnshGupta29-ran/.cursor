# Harborline Dispatch – Sentiment Triage Inbox

## Quickstart

```bash
# Install dependencies (Node.js 20+ required)
npm install

# Run the server
npm start   # listens on http://127.0.0.1:5000
```

The service is API‑only; no UI is shipped. Use the provided `curl` examples to interact.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health‑check (`{status:"ok"}`) |
| `POST` | `/tickets` | Create a ticket and receive classification. Body JSON: `{channel,author_handle,subject,body}` |
| `GET` | `/queues/:name/tickets` | List tickets routed to a given queue (`safety`, `fare-billing`, `fleet-damage`, `accessibility`, `general`). |
| `GET` | `/stats` | Aggregated stats: total tickets, per‑queue counts, urgency histogram, review‑lane count. |
| `GET` | `/export` | JSON bundle of the entire SQLite state (versioned). |
| `POST` | `/import` | Restore state from a bundle; must be version 1. |

All responses use JSON error objects `{error:{code, message}}` for 4xx/5xx cases.

## Lexicons & Configuration

Lexicon files live under `src/lexicon/`:
- `sentiment.json` – positive / negative terms.
- `urgency.json` – four urgency levels (`p1`‑`p4`).
- `categories.json` – keywords mapping to queues.

Routing thresholds and queue precedence are defined in `src/config/routing.json`.

## Testing

```bash
npm test   # runs the built‑in test suite (node --test)
```
The test boots the server, creates a ticket, checks that it routes to the `safety` queue, performs an export, wipes the DB via an empty import, and verifies the stats are reset.

## Static Preview

```bash
npm run preview   # generates preview/index.html
```
The preview classifies the fixture messages in `fixtures/` and writes a self‑contained HTML report (`preview/index.html`). Open it in any browser – no server required.

## Fixtures

`fixtures/msg1.txt` – example rider message used by the preview and seed script.

## Seed Script

```bash
npm run seed   # POSTs all fixture messages to the running server
```

## Limitations

- Deterministic lexicon‑based scoring only; no ML models or external APIs.
- English‑only tokenisation; no handling of sarcasm or complex language.
- No authentication – single‑operator local tool.
- SQLite file stored at `data/harborline.db`; migrations run automatically on start.

## How to Replace the Lexicon Scorer

Replace the `classify` function in `src/server.js` with a call to your own model. Keep the returned shape (`sentiment`, `urgency`, `category`, `confidence`, `evidence`) and the `reviewConfidence` threshold logic to retain API compatibility.
