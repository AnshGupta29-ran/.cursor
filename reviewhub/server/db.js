import Database from 'better-sqlite3';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
export const DB_PATH = process.env.DB_PATH || path.join(here, '..', 'data', 'reviewhub.db');
if (DB_PATH !== ':memory:') fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });

export const db = new Database(DB_PATH);
// WAL: readers never block the single writer — matters once WS fanout and API
// reads overlap. Foreign keys ON because SQLite ships with them off.
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

export function migrate() {
  db.exec(fs.readFileSync(path.join(here, 'schema.sql'), 'utf8'));
}
migrate();

// Every security-relevant mutation calls this. Centralizing it means no route
// can "forget" to audit — the helper is one line, so there's no excuse not to.
export function audit(userId, action, entity, entityId, metadata = {}) {
  db.prepare('INSERT INTO audit_log (user_id, action, entity, entity_id, metadata) VALUES (?,?,?,?,?)')
    .run(userId ?? null, action, entity, entityId ?? null, JSON.stringify(metadata));
}
