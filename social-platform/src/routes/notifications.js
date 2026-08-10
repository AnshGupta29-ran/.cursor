import { Router } from 'express';
import { all, get, run } from '../db.js';
import { requireAuth } from '../auth/middleware.js';
import { pagination, paginated } from '../utils/http.js';

export const notificationsRouter = Router();

notificationsRouter.get('/notifications', requireAuth, (req, res) => {
  const { limit, offset } = pagination(req, 30);
  const unreadOnly = req.query.unread === '1';
  const rows = all(
    `SELECT n.id, n.type, n.entity_id, n.read, n.created_at,
            a.id AS actor_id, a.username AS actor_username, a.display_name AS actor_display_name, a.avatar_url AS actor_avatar
     FROM notifications n LEFT JOIN users a ON a.id = n.actor_id
     WHERE n.user_id = ? ${unreadOnly ? 'AND n.read = 0' : ''}
     ORDER BY n.created_at DESC, n.id DESC LIMIT ? OFFSET ?`,
    req.user.id, limit, offset
  );
  res.json(paginated(rows.map((r) => ({
    id: r.id,
    type: r.type,
    entity_id: r.entity_id,
    read: !!r.read,
    created_at: r.created_at,
    actor: r.actor_id ? { id: r.actor_id, username: r.actor_username, display_name: r.actor_display_name, avatar_url: r.actor_avatar } : null,
  })), { limit, offset }));
});

notificationsRouter.get('/notifications/unread-count', requireAuth, (req, res) => {
  const { c } = get('SELECT COUNT(*) AS c FROM notifications WHERE user_id = ? AND read = 0', req.user.id);
  res.json({ unread: c });
});

notificationsRouter.post('/notifications/read', requireAuth, (req, res) => {
  const ids = Array.isArray(req.body?.ids) ? req.body.ids.filter((n) => Number.isInteger(n)) : null;
  if (ids && ids.length) {
    const marks = ids.map(() => '?').join(',');
    run(`UPDATE notifications SET read = 1 WHERE user_id = ? AND id IN (${marks})`, req.user.id, ...ids);
  } else {
    run('UPDATE notifications SET read = 1 WHERE user_id = ?', req.user.id);
  }
  const { c } = get('SELECT COUNT(*) AS c FROM notifications WHERE user_id = ? AND read = 0', req.user.id);
  res.json({ unread: c });
});
