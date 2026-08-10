// One subscriber translates domain events into three delivery channels:
// DB row (in-app inbox), WebSocket push (realtime), email (offline reach).
// Deduplication rule: never notify a user about their own action.
import { bus } from './events.js';
import { db } from './db.js';
import { sendEmail } from './email.js';

let wsPush = () => {};
export function registerWebSocket(fn) { wsPush = fn; }

function deliver(userId, type, message, payload) {
  db.prepare('INSERT INTO notifications (user_id, type, message, payload) VALUES (?,?,?,?)')
    .run(userId, type, message, JSON.stringify(payload));
  wsPush(userId, { type: 'notification', notification: { type, message, payload } });
  const user = db.prepare('SELECT email FROM users WHERE id = ?').get(userId);
  if (user) sendEmail(user.email, `[ReviewHub] ${type}`, message);
}

const reviewersOf = prId =>
  db.prepare('SELECT reviewer_id AS id FROM reviews WHERE pr_id = ?').all(prId).map(r => r.id);

const authorOf = prId =>
  db.prepare('SELECT author_id FROM pull_requests WHERE id = ?').get(prId)?.author_id;

bus.on('pr.created', ({ pr, actor }) => {
  // Notify all teammates except the author — a new PR is everyone's business once.
  const members = db.prepare('SELECT user_id FROM team_members WHERE team_id = (SELECT team_id FROM repositories WHERE id = ?)').all(pr.repo_id);
  for (const m of members) {
    if (m.user_id !== actor.id) deliver(m.user_id, 'pr.created', `${actor.username} opened PR #${pr.number}: ${pr.title}`, { prId: pr.id });
  }
});

bus.on('pr.comment', ({ pr, comment, actor }) => {
  const targets = new Set([authorOf(pr.id), ...reviewersOf(pr.id)]);
  targets.delete(actor.id);
  for (const id of targets) {
    if (id) deliver(id, 'pr.comment', `${actor.username} commented on PR #${pr.number}`, { prId: pr.id });
  }
});

bus.on('pr.review', ({ pr, review, actor }) => {
  const author = authorOf(pr.id);
  if (author && author !== actor.id) {
    deliver(author, `pr.${review.state}`, `${actor.username} ${review.state.replace('_', ' ')} on PR #${pr.number}`, { prId: pr.id });
  }
});

bus.on('pr.status', ({ pr, actor }) => {
  const targets = new Set([authorOf(pr.id), ...reviewersOf(pr.id)]);
  targets.delete(actor.id);
  for (const id of targets) {
    if (id) deliver(id, `pr.${pr.status}`, `PR #${pr.number} (${pr.title}) was ${pr.status}`, { prId: pr.id });
  }
});
