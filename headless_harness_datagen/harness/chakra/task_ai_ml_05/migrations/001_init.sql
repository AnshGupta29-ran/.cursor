BEGIN TRANSACTION;
-- Tickets table
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    author_handle TEXT,
    subject TEXT,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL
);
-- Classifications table
CREATE TABLE IF NOT EXISTS classifications (
    ticket_id TEXT PRIMARY KEY,
    sentiment TEXT NOT NULL,
    sentiment_score REAL NOT NULL,
    urgency TEXT NOT NULL,
    urgency_score REAL NOT NULL,
    category TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence TEXT NOT NULL, -- JSON array string
    FOREIGN KEY(ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);
-- Queues table (static)
CREATE TABLE IF NOT EXISTS queues (
    name TEXT PRIMARY KEY,
    description TEXT,
    sla_minutes INTEGER,
    precedence INTEGER
);
-- Audit log
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    payload TEXT,
    ts TEXT NOT NULL
);
COMMIT;