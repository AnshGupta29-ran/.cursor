import { Router } from 'express';
import { all, get } from '../db.js';
import { requireAuth, requireRole } from '../auth/middleware.js';
import { notFound } from '../utils/http.js';
import { track } from '../utils/analytics.js';
import { onlineUserIds } from '../realtime.js';

export const analyticsRouter = Router();

// Mobile SDKs can report client-side events (screen views, taps) here.
analyticsRouter.post('/analytics/events', requireAuth, (req, res) => {
  const events = Array.isArray(req.body?.events) ? req.body.events.slice(0, 50) : [];
  for (const e of events) {
    if (typeof e?.event === 'string' && e.event.length <= 60) {
      track(e.event, {
        userId: req.user.id,
        entityType: typeof e.entity_type === 'string' ? e.entity_type.slice(0, 30) : null,
        entityId: Number.isInteger(e.entity_id) ? e.entity_id : null,
      });
    }
  }
  res.status(202).json({ accepted: events.length });
});

// My engagement stats as a creator.
analyticsRouter.get('/analytics/me', requireAuth, (req, res) => {
  const uid = req.user.id;
  res.json({
    posts: get('SELECT COUNT(*) AS c FROM posts WHERE user_id = ? AND hidden = 0', uid).c,
    likes_received: get('SELECT COUNT(*) AS c FROM likes l JOIN posts p ON p.id = l.post_id WHERE p.user_id = ?', uid).c,
    comments_received: get('SELECT COUNT(*) AS c FROM comments c JOIN posts p ON p.id = c.post_id WHERE p.user_id = ? AND c.hidden = 0', uid).c,
    followers: get('SELECT COUNT(*) AS c FROM follows WHERE followee_id = ?', uid).c,
    following: get('SELECT COUNT(*) AS c FROM follows WHERE follower_id = ?', uid).c,
    post_views_30d: get(
      `SELECT COUNT(*) AS c FROM analytics_events WHERE event = 'post_view'
         AND entity_type = 'post' AND entity_id IN (SELECT id FROM posts WHERE user_id = ?)
         AND created_at >= datetime('now', '-30 days')`, uid
    ).c,
  });
});

// Per-post breakdown (author or staff).
analyticsRouter.get('/analytics/posts/:id', requireAuth, (req, res, next) => {
  try {
    const post = get('SELECT id, user_id FROM posts WHERE id = ?', req.params.id);
    if (!post) throw notFound('Post not found');
    if (post.user_id !== req.user.id && !['moderator', 'admin'].includes(req.user.role)) {
      return res.status(403).json({ error: { code: 'forbidden', message: 'Not your post' } });
    }
    res.json({
      post_id: post.id,
      likes: get('SELECT COUNT(*) AS c FROM likes WHERE post_id = ?', post.id).c,
      comments: get('SELECT COUNT(*) AS c FROM comments WHERE post_id = ? AND hidden = 0', post.id).c,
      views: get(`SELECT COUNT(*) AS c FROM analytics_events WHERE event = 'post_view' AND entity_type = 'post' AND entity_id = ?`, post.id).c,
      views_by_day: all(
        `SELECT date(created_at) AS day, COUNT(*) AS views FROM analytics_events
         WHERE event = 'post_view' AND entity_type = 'post' AND entity_id = ?
         GROUP BY day ORDER BY day DESC LIMIT 30`, post.id
      ),
    });
  } catch (e) { next(e); }
});

// Platform overview — staff only.
analyticsRouter.get('/analytics/overview', requireAuth, requireRole('moderator', 'admin'), (req, res) => {
  const days = Math.min(Math.max(parseInt(req.query.days, 10) || 7, 1), 90);
  res.json({
    online_now: onlineUserIds().length,
    totals: {
      users: get('SELECT COUNT(*) AS c FROM users').c,
      posts: get('SELECT COUNT(*) AS c FROM posts WHERE hidden = 0').c,
      comments: get('SELECT COUNT(*) AS c FROM comments WHERE hidden = 0').c,
      likes: get('SELECT COUNT(*) AS c FROM likes').c,
      messages: get('SELECT COUNT(*) AS c FROM messages').c,
      open_reports: get(`SELECT COUNT(*) AS c FROM reports WHERE status = 'open'`).c,
    },
    signups_by_day: all(
      `SELECT date(created_at) AS day, COUNT(*) AS count FROM users
       WHERE created_at >= datetime('now', ?) GROUP BY day ORDER BY day`, `-${days} days`
    ),
    activity_by_day: all(
      `SELECT date(created_at) AS day, event, COUNT(*) AS count FROM analytics_events
       WHERE created_at >= datetime('now', ?)
         AND event IN ('post_create','comment_create','like','follow','message_send','login')
       GROUP BY day, event ORDER BY day`, `-${days} days`
    ),
    top_posts_7d: all(
      `SELECT p.id, p.content, u.username,
              (SELECT COUNT(*) FROM likes l WHERE l.post_id = p.id) AS likes,
              (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id AND c.hidden = 0) AS comments
       FROM posts p JOIN users u ON u.id = p.user_id
       WHERE p.hidden = 0 AND p.created_at >= datetime('now', '-7 days')
       ORDER BY likes DESC, comments DESC LIMIT 10`
    ),
  });
});
