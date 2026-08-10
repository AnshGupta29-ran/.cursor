# Social Platform API

A complete social media backend: user profiles, posts & comments, follow system, ranked feed, notifications, direct messaging, content moderation, and analytics — exposed as a mobile-ready REST + WebSocket API.

Built with **Node.js + Express + SQLite** (via the built-in `node:sqlite` — no native compilation). Requires **Node >= 22.5**.

## Quick start

```bash
npm install
cp .env.example .env   # optional; defaults work out of the box
npm run seed           # optional demo data (users alice/bob/carol/dave/erin, password: password123)
npm start              # serves on http://0.0.0.0:3000
npm run smoke          # end-to-end test of every feature area
```

## Conventions

- **Auth**: `Authorization: Bearer <token>` from `/api/auth/register` or `/api/auth/login`.
- **Pagination**: `?limit=20&offset=0` on list endpoints → responses are `{ data: [...], page: { limit, offset, count } }`.
- **Errors**: always `{ error: { code, message } }` with a matching HTTP status.
- **Realtime**: connect to `ws://<host>:3000/ws?token=<jwt>`. Server pushes `notification`, `message`, and `read_receipt` frames. Send `{"type":"ping"}` to keep alive.

## Endpoints

### Auth
| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account → `{ token, user }` |
| POST | `/api/auth/login` | Login with username or email |
| GET | `/api/auth/me` | Current user |
| POST | `/api/auth/change-password` | Change password |

### Profiles & follows
| Method | Path | Description |
|---|---|---|
| GET / PATCH | `/api/me/profile` | Read/update my profile (display_name, bio, avatar_url) |
| GET | `/api/users/:id` | Public profile + counts + `is_following`/`follows_you` |
| GET | `/api/users/:id/posts` | A user's posts |
| GET | `/api/search/users?q=` | Search users |
| POST / DELETE | `/api/users/:id/follow` | Follow / unfollow |
| GET | `/api/users/:id/followers` · `/api/users/:id/following` | Follow lists |
| GET | `/api/suggestions/users` | Who-to-follow (mutuals + popularity) |

### Posts & comments
| Method | Path | Description |
|---|---|---|
| POST / GET / DELETE | `/api/posts`, `/api/posts/:id` | Create / read / delete posts |
| POST / DELETE | `/api/posts/:id/like` | Like / unlike |
| POST / GET | `/api/posts/:id/comments` | Add (supports `parent_id` threads) / list comments |
| DELETE | `/api/comments/:id` | Delete own comment |

### Feed
| Method | Path | Description |
|---|---|---|
| GET | `/api/feed` | Ranked home feed. Score = engagement × recency decay (12h half-life) × follow/affinity boost |
| GET | `/api/feed?mode=latest` | Chronological feed of followed authors |
| GET | `/api/feed/explore` | Trending platform-wide |

### Notifications
| Method | Path | Description |
|---|---|---|
| GET | `/api/notifications` · `?unread=1` | List notifications (like, comment, follow, mention, message, moderation) |
| GET | `/api/notifications/unread-count` | Badge count |
| POST | `/api/notifications/read` | `{ ids: [...] }` or all |

### Messaging
| Method | Path | Description |
|---|---|---|
| GET / POST | `/api/conversations` | List (with unread counts) / open with `{ user_id }` |
| GET / POST | `/api/conversations/:id/messages` | History / send |
| POST | `/api/conversations/:id/read` | Mark read (sends read receipt over WS) |

### Moderation
| Method | Path | Description |
|---|---|---|
| POST | `/api/reports` | Report a post/comment/user. 3 open reports auto-hides content |
| GET | `/api/moderation/reports?status=open` | Staff queue (moderator/admin) |
| POST | `/api/moderation/reports/:id/resolve` | Resolve or `{ dismiss: true }` |
| POST | `/api/moderation/hide` · `/restore` | Hide/restore posts & comments |
| POST | `/api/moderation/users/:id/status` | Admin: `{ status: active\|muted\|banned }` |
| GET / POST / DELETE | `/api/moderation/banned-words[/:word]` | Manage auto-filter wordlist |
| GET | `/api/moderation/log` | Audit trail |

### Analytics
| Method | Path | Description |
|---|---|---|
| POST | `/api/analytics/events` | Client event batch (max 50) |
| GET | `/api/analytics/me` | My creator stats |
| GET | `/api/analytics/posts/:id` | Per-post views/likes/comments |
| GET | `/api/analytics/overview?days=7` | Staff: platform totals, signups, activity, top posts |

### Meta
| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/api` | API name/version |

## Example session

```bash
# Register
TOKEN=$(curl -s -X POST localhost:3000/api/auth/register \
  -H 'content-type: application/json' \
  -d '{"username":"jane","email":"jane@x.com","password":"password123"}' | jq -r .token)

# Post
curl -X POST localhost:3000/api/posts -H "authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' -d '{"content":"hello feed"}'

# Feed
curl localhost:3000/api/feed -H "authorization: Bearer $TOKEN"

# WebSocket (Node)
node -e 'new (require("ws"))("ws://localhost:3000/ws?token='$TOKEN'").on("message",d=>console.log(String(d)))'
```

## Architecture notes

- `src/db.js` — schema + prepared-statement helpers; WAL mode, foreign keys on.
- `src/utils/crypto.js` — scrypt password hashing and HS256 JWT (no external deps).
- `src/realtime.js` — WebSocket hub keyed by user; REST remains the source of truth so messages/notifications persist for offline users.
- `src/utils/moderation.js` — wordlist filter applied to posts, comments, and DMs before insert.
- `src/utils/analytics.js` — fire-and-forget event tracking; never fails a request.
- Roles: `user` < `moderator` (queue, hide/restore) < `admin` (sanctions, overview). First run creates `admin`/`admin123` from `.env` — change it.
- SQLite keeps this zero-setup. The SQL is standard; porting to Postgres means swapping `db.js` and the `julianday`/`strftime` date functions in `feed.js` and `messages.js`.
