# ReviewHub

A collaborative code review platform: pull requests with diffs, inline threaded
comments, approval gates, review checklists, real-time updates, notifications,
audit logging, and team analytics.

## Architecture

Modular monolith (Node + Express + better-sqlite3) with an in-process event bus:
routes mutate state and emit events; notifications, email and WebSocket fanout
subscribe. The bus is the future extraction point — point it at Redis pub/sub
and notify/analytics become separate services with no route changes.

```
server/
  index.js     app assembly, static hosting, error shape
  db.js        SQLite (WAL), schema load, audit helper
  schema.sql   tables, indexes (chosen from real query patterns)
  auth.js      register/login, JWT middleware, team RBAC
  routes.js    teams, repos, PRs, comments, reviews, checklist, notifications
  analytics.js team metrics (time-to-first-review, approval rate, stale PRs, load)
  events.js    in-process bus
  notify.js    event -> DB notification + WS push + email
  ws.js        JWT-authed WebSocket, user + PR channels
  email.js     provider interface (console stub; SMTP/SES in prod)
  seed.js      demo data
public/        dependency-free SPA (hash router, diff parser, inline comments)
tests/         node:test integration suite (real HTTP + in-memory DB)
```

## Key decisions

- **Merge gate is server-enforced**: open status + maintainer role + >=1 approval
  + zero open change-requests. The UI hides the button; the server is the authority.
- **Authors cannot review their own PRs** — "approved" must be a signal.
- **Diffs stored as unified-diff text**, parsed once into a line model shared by
  rendering and comment anchoring (anchors are new-file line numbers, meaningful
  after merge).
- **All user content rendered via textContent** — injection-proof by construction.
- **Append-only audit_log** written on every security-relevant mutation.
- **JWT (12h) authenticates both HTTP and the WebSocket upgrade.**

## Run

```bash
npm install
npm run seed     # demo data: alice/bob/carol, password123
npm start        # http://localhost:3000
npm test         # integration suite
```

## Docker

```bash
docker compose up --build
```

Set `JWT_SECRET` in the environment for anything beyond local use (`.env.example`).

## Production path (documented, not built)

1. Swap better-sqlite3 for Postgres behind the same portable queries.
2. Redis: cache hot endpoints + WS fanout across multiple API nodes.
3. GitHub/GitLab OAuth for SSO and repo sync (provider field already modeled).
4. Nightly rollup table for analytics at scale.
5. TLS termination + rate limiting at a reverse proxy in front of the app.
