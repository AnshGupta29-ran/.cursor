import { Router } from 'express';
import { all, get, run } from '../db.js';
import { requireAuth, requireRole } from '../auth/middleware.js';
import { badRequest, notFound, pagination, paginated } from '../utils/http.js';
import { notify } from '../utils/notify.js';
import { invalidateWordCache } from '../utils/moderation.js';

export const moderationRouter = Router();
const staffOnly = [requireAuth, requireRole('moderator', 'admin')];

function targetExists(type, id) {
  if (type === 'post') return get('SELECT id, user_id FROM posts WHERE id = ?', id);
  if (type === 'comment') return get('SELECT id, user_id FROM comments WHERE id = ?', id);
  if (type === 'user') return get('SELECT id, id AS user_id FROM users WHERE id = ?', id);
  return null;
}

function logAction(adminId, action, targetType, targetId, note = '') {
  run('INSERT INTO moderation_log (admin_id, action, target_type, target_id, note) VALUES (?,?,?,?,?)',
    adminId, action, targetType, targetId, note);
}

// ---- Anyone can report ----

moderationRouter.post('/reports', requireAuth, (req, res, next) => {
  try {
    const { target_type, target_id, reason } = req.body || {};
    if (!['post', 'comment', 'user'].includes(target_type)) throw badRequest('target_type must be post, comment, or user');
    const target = targetExists(target_type, Number(target_id));
    if (!target) throw notFound('Report target not found');
    const text = String(reason || '').trim();
    if (!text) throw badRequest('reason is required');
    if (text.length > 1000) throw badRequest('reason too long');

    const info = run('INSERT INTO reports (reporter_id, target_type, target_id, reason) VALUES (?,?,?,?)',
      req.user.id, target_type, target_id, text);

    // Auto-escalate: hide content once it accumulates 3+ open reports.
    if (target_type !== 'user') {
      const { c } = get('SELECT COUNT(*) AS c FROM reports WHERE target_type = ? AND target_id = ? AND status = \'open\'',
        target_type, target_id);
      if (c >= 3) {
        run(`UPDATE ${target_type === 'post' ? 'posts' : 'comments'} SET hidden = 1 WHERE id = ?`, target_id);
        logAction(req.user.id, 'auto_hide', target_type, target_id, `${c} open reports`);
        notify(target.user_id, null, 'moderation', target_id);
      }
    }
    res.status(201).json({ report: { id: Number(info.lastInsertRowid), status: 'open' } });
  } catch (e) { next(e); }
});

// ---- Staff queue ----

moderationRouter.get('/moderation/reports', ...staffOnly, (req, res) => {
  const { limit, offset } = pagination(req, 30);
  const status = ['open', 'resolved', 'dismissed'].includes(req.query.status) ? req.query.status : 'open';
  const rows = all(
    `SELECT r.*, ru.username AS reporter_username
     FROM reports r JOIN users ru ON ru.id = r.reporter_id
     WHERE r.status = ? ORDER BY r.created_at ASC LIMIT ? OFFSET ?`,
    status, limit, offset
  );
  res.json(paginated(rows, { limit, offset }));
});

moderationRouter.post('/moderation/reports/:id/resolve', ...staffOnly, (req, res, next) => {
  try {
    const report = get('SELECT * FROM reports WHERE id = ?', req.params.id);
    if (!report) throw notFound('Report not found');
    run('UPDATE reports SET status = ? WHERE id = ?', req.body?.dismiss ? 'dismissed' : 'resolved', report.id);
    logAction(req.user.id, req.body?.dismiss ? 'dismiss_report' : 'resolve_report', report.target_type, report.target_id, `report #${report.id}`);
    res.json({ ok: true });
  } catch (e) { next(e); }
});

// ---- Content actions ----

moderationRouter.post('/moderation/hide', ...staffOnly, (req, res, next) => {
  try {
    const { target_type, target_id, note } = req.body || {};
    if (!['post', 'comment'].includes(target_type)) throw badRequest('target_type must be post or comment');
    const target = targetExists(target_type, Number(target_id));
    if (!target) throw notFound('Target not found');
    run(`UPDATE ${target_type === 'post' ? 'posts' : 'comments'} SET hidden = 1 WHERE id = ?`, target_id);
    logAction(req.user.id, 'hide', target_type, target_id, String(note || ''));
    notify(target.user_id, null, 'moderation', Number(target_id));
    res.json({ ok: true });
  } catch (e) { next(e); }
});

moderationRouter.post('/moderation/restore', ...staffOnly, (req, res, next) => {
  try {
    const { target_type, target_id } = req.body || {};
    if (!['post', 'comment'].includes(target_type)) throw badRequest('target_type must be post or comment');
    const target = targetExists(target_type, Number(target_id));
    if (!target) throw notFound('Target not found');
    run(`UPDATE ${target_type === 'post' ? 'posts' : 'comments'} SET hidden = 0 WHERE id = ?`, target_id);
    logAction(req.user.id, 'restore', target_type, target_id);
    res.json({ ok: true });
  } catch (e) { next(e); }
});

// ---- User sanctions (admin only) ----

moderationRouter.post('/moderation/users/:id/status', requireAuth, requireRole('admin'), (req, res, next) => {
  try {
    const { status } = req.body || {};
    if (!['active', 'muted', 'banned'].includes(status)) throw badRequest('status must be active, muted, or banned');
    const target = get('SELECT id, role FROM users WHERE id = ?', req.params.id);
    if (!target) throw notFound('User not found');
    if (target.role === 'admin' && status !== 'active') throw badRequest('Cannot sanction an admin');
    run('UPDATE users SET status = ? WHERE id = ?', status, target.id);
    logAction(req.user.id, `user_${status}`, 'user', target.id);
    notify(target.id, null, 'moderation', target.id);
    res.json({ ok: true, status });
  } catch (e) { next(e); }
});

// ---- Banned word list ----

moderationRouter.get('/moderation/banned-words', ...staffOnly, (req, res) => {
  res.json({ data: all('SELECT word FROM banned_words ORDER BY word').map((r) => r.word) });
});

moderationRouter.post('/moderation/banned-words', ...staffOnly, (req, res, next) => {
  try {
    const word = String(req.body?.word || '').trim().toLowerCase();
    if (!word || word.length > 100) throw badRequest('word is required (max 100 chars)');
    run('INSERT OR IGNORE INTO banned_words (word) VALUES (?)', word);
    invalidateWordCache();
    logAction(req.user.id, 'ban_word', 'user', 0, word);
    res.status(201).json({ ok: true });
  } catch (e) { next(e); }
});

moderationRouter.delete('/moderation/banned-words/:word', ...staffOnly, (req, res) => {
  run('DELETE FROM banned_words WHERE word = ?', req.params.word.toLowerCase());
  invalidateWordCache();
  res.json({ ok: true });
});

// ---- Audit trail ----

moderationRouter.get('/moderation/log', ...staffOnly, (req, res) => {
  const { limit, offset } = pagination(req, 50);
  const rows = all(
    `SELECT l.*, u.username AS admin_username
     FROM moderation_log l JOIN users u ON u.id = l.admin_id
     ORDER BY l.created_at DESC, l.id DESC LIMIT ? OFFSET ?`,
    limit, offset
  );
  res.json(paginated(rows, { limit, offset }));
});
