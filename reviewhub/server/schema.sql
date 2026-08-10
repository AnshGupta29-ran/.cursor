-- ReviewHub schema. SQLite dialect, written to stay Postgres-portable
-- (no SQLite-only types; INTEGER PKs map to SERIAL/IDENTITY).
-- Design rule: every entity that a user can act on gets created_at and an audit trail.

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  display_name TEXT NOT NULL DEFAULT '',
  role TEXT NOT NULL DEFAULT 'member', -- site-level: 'admin' | 'member'
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS teams (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  created_by INTEGER NOT NULL REFERENCES users(id),
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Team membership carries the RBAC role. Three roles is deliberate:
-- enough to express "can review" vs "can merge" without a policy engine.
CREATE TABLE IF NOT EXISTS team_members (
  team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL DEFAULT 'member', -- 'owner' | 'maintainer' | 'member'
  PRIMARY KEY (team_id, user_id)
);

CREATE TABLE IF NOT EXISTS repositories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  provider TEXT NOT NULL DEFAULT 'manual', -- 'github' | 'gitlab' | 'manual'
  name TEXT NOT NULL,
  url TEXT NOT NULL DEFAULT '',
  default_branch TEXT NOT NULL DEFAULT 'main',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (team_id, name)
);

CREATE TABLE IF NOT EXISTS pull_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  repo_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
  number INTEGER NOT NULL, -- per-repo human-friendly number, like GitHub
  title TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  author_id INTEGER NOT NULL REFERENCES users(id),
  source_branch TEXT NOT NULL DEFAULT 'feature',
  target_branch TEXT NOT NULL DEFAULT 'main',
  status TEXT NOT NULL DEFAULT 'open', -- state machine: open -> merged | closed (-> open on reopen)
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (repo_id, number)
);

-- Diffs are stored as unified-diff patches. We deliberately store text, not blobs:
-- patches are what reviews discuss, and they compress the change to its essence.
CREATE TABLE IF NOT EXISTS pr_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pr_id INTEGER NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
  path TEXT NOT NULL,
  patch TEXT NOT NULL
);

-- file_id NULL  = general PR comment
-- file_id set + line_number NULL = file-level comment
-- file_id set + line_number set  = inline comment anchored to a NEW-file line
-- parent_id enables threads; resolved enables the "feedback isn't lost" workflow.
CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pr_id INTEGER NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
  file_id INTEGER REFERENCES pr_files(id) ON DELETE CASCADE,
  line_number INTEGER,
  parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
  author_id INTEGER NOT NULL REFERENCES users(id),
  body TEXT NOT NULL,
  resolved INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- One live review per reviewer per PR: re-reviewing UPSERTs, so "latest state
-- per reviewer" is always a single row — the merge gate reads it directly.
CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pr_id INTEGER NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
  reviewer_id INTEGER NOT NULL REFERENCES users(id),
  state TEXT NOT NULL, -- 'approved' | 'changes_requested' | 'commented'
  body TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (pr_id, reviewer_id)
);

CREATE TABLE IF NOT EXISTS review_checklists (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pr_id INTEGER NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
  item TEXT NOT NULL,
  checked INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type TEXT NOT NULL,
  message TEXT NOT NULL,
  payload TEXT NOT NULL DEFAULT '{}',
  read INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Audit log: who did what to which entity. Written on every security-relevant
-- mutation. Append-only by convention (no UPDATE/DELETE endpoints exist).
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id),
  action TEXT NOT NULL,
  entity TEXT NOT NULL,
  entity_id INTEGER,
  metadata TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes chosen from the actual query patterns in routes.js — not speculative.
CREATE INDEX IF NOT EXISTS idx_pr_repo_status ON pull_requests(repo_id, status);
CREATE INDEX IF NOT EXISTS idx_files_pr ON pr_files(pr_id);
CREATE INDEX IF NOT EXISTS idx_comments_pr ON comments(pr_id);
CREATE INDEX IF NOT EXISTS idx_notif_user_read ON notifications(user_id, read);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity, entity_id);
CREATE INDEX IF NOT EXISTS idx_members_user ON team_members(user_id);
