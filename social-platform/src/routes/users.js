import { Router } from 'express';
import { all, get, run } from '../db.js';
import { requireAuth, requireNotMuted } from '../auth/middleware.js';
import { badRequest, notFound, pagination, paginated, publicUser } from '../utils/http.js';
import { track } from '../utils/analytics.js';
import { notify } from '../utils/notify.js';
import { pushToUser } from '../realtime.js';

export const usersRouter = Router();

const COUNTS = `
  (SELECT COUNT(*) FROM follows f WHERE f.followee_id = u.id) AS follower_count,
  (SELECT COUNT(*) FROM follows f WHERE f.follower_id = u.id) AS following_count,
  (SELECT COUNT(*) FROM posts p WHERE p.user_id = u.id AND p.hidden = 0) AS post_count
`;

// ---- Profile management ----

usersRouter.get('/me/profile', requireAuth, (req, res) => {
  const row = get(`SELECT u.*, ${COUNTS} FROM users u WHERE u.id = ?`, req.user.id);
  res.json({ user: publicUser(row, { email: row.email, role: row.role, status: row.status, follower_count: row.follower_count, following_count: row.following_count, post_count: row.post_count }) });
});

usersRouter.patch('/me/profile', requireAuth, (req, res, next) => {
  try {
    const { display_name, bio, avatar_url } = req.body || {};
    if (display_name !== undefined && String(display_name).length > 60) throw badRequest('display_name too long (max 60)');
    if (bio !== undefined && String(bio).length > 500) throw badRequest('bio too long (max 500)');
    if (avatar_url !== undefined && String(avatar_url).length > 500) throw badRequest('avatar_url too long');
    run(
      `UPDATE users SET
         display_name = COALESCE(?, display_name),
         bio          = COALESCE(?, bio),
         avatar_url   = COALESCE(?, avatar_url)
       WHERE id = ?`,
      display_name ?? null, bio ?? null, avatar_url ?? null, req.user.id
    );
    const row = get(`SELECT u.*, ${COUNTS} FROM users u WHERE u.id = ?`, req.user.id);
    res.json({ user: publicUser(row, { follower_count: row.follower_count, following_count: row.following_count, post_count: row.post_count }) });
  } catch (e) { next(e); }
});

// ---- Public profiles ----

usersRouter.get('/users/:id', requireAuth, (req, res, next) => {
  try {
    const row = get(`SELECT u.*, ${COUNTS} FROM users u WHERE u.id = ?`, req.params.id);
    if (!row || row.status === 'banned') throw notFound('User not found');
    const rel = get('SELECT 1 FROM follows WHERE follower_id = ? AND followee_id = ?', req.user.id, row.id);
    const followsYou = get('SELECT 1 FROM follows WHERE follower_id = ? AND followee_id = ?', row.id, req.user.id);
    track('profile_view', { userId: req.user.id, entityType: 'user', entityId: row.id });
    res.json({
      user: publicUser(row, {
        follower_count: row.follower_count,
        following_count: row.following_count,
        post_count: row.post_count,
        is_following: !!rel,
        follows_you: !!followsYou,
      }),
    });
  } catch (e) { next(e); }
});

usersRouter.get('/users/:id/posts', requireAuth, (req, res, next) => {
  try {
    const target = get('SELECT id FROM users WHERE id = ? AND status != \'banned\'', req.params.id);
    if (!target) throw notFound('User not found');
    const { limit, offset } = pagination(req);
    const rows = all(
      `SELECT p.id, p.user_id, p.content, p.media_url, p.created_at,
              u.username, u.display_name, u.avatar_url,
              (SELECT COUNT(*) FROM likes l WHERE l.post_id = p.id) AS like_count,
              (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id AND c.hidden = 0) AS comment_count,
              EXISTS(SELECT 1 FROM likes l WHERE l.post_id = p.id AND l.user_id = ?) AS liked_by_me
       FROM posts p JOIN users u ON u.id = p.user_id
       WHERE p.user_id = ? AND p.hidden = 0
       ORDER BY p.created_at DESC, p.id DESC LIMIT ? OFFSET ?`,
      req.user.id, req.params.id, limit, offset
    );
    res.json(paginated(rows.map(shapePost), { limit, offset }));
  } catch (e) { next(e); }
});

usersRouter.get('/search/users', requireAuth, (req, res, next) => {
  try {
    const q = String(req.query.q || '').trim();
    if (!q) throw badRequest('q is required');
    const { limit, offset } = pagination(req);
    const rows = all(
      `SELECT u.*, ${COUNTS} FROM users u
       WHERE u.status != 'banned' AND (u.username LIKE ? OR u.display_name LIKE ?)
       ORDER BY follower_count DESC, u.username LIMIT ? OFFSET ?`,
      `%${q}%`, `%${q}%`, limit, offset
    );
    res.json(paginated(rows.map((r) => publicUser(r, { follower_count: r.follower_count })), { limit, offset }));
  } catch (e) { next(e); }
});

// ---- Follow system ----

usersRouter.post('/users/:id/follow', requireAuth, requireNotMuted, (req, res, next) => {
  try {
    const target = get('SELECT id, status FROM users WHERE id = ?', req.params.id);
    if (!target || target.status === 'banned') throw notFound('User not found');
    if (target.id === req.user.id) throw badRequest('You cannot follow yourself');
    const existing = get('SELECT 1 FROM follows WHERE follower_id = ? AND followee_id = ?', req.user.id, target.id);
    if (!existing) {
      run('INSERT INTO follows (follower_id, followee_id) VALUES (?,?)', req.user.id, target.id);
      track('follow', { userId: req.user.id, entityType: 'user', entityId: target.id });
      notify(target.id, req.user.id, 'follow', req.user.id);
    }
    const counts = get(`SELECT ${COUNTS} FROM users u WHERE u.id = ?`, target.id);
    res.json({ following: true, follower_count: counts.follower_count });
  } catch (e) { next(e); }
});

usersRouter.delete('/users/:id/follow', requireAuth, (req, res, next) => {
  try {
    run('DELETE FROM follows WHERE follower_id = ? AND followee_id = ?', req.user.id, req.params.id);
    const counts = get(`SELECT ${COUNTS} FROM users u WHERE u.id = ?`, req.params.id);
    res.json({ following: false, follower_count: counts?.follower_count ?? 0 });
  } catch (e) { next(e); }
});

usersRouter.get('/users/:id/followers', requireAuth, (req, res, next) => {
  try {
    const { limit, offset } = pagination(req);
    const rows = all(
      `SELECT u.*, EXISTS(SELECT 1 FROM follows f WHERE f.follower_id = ? AND f.followee_id = u.id) AS is_following
       FROM follows f JOIN users u ON u.id = f.follower_id
       WHERE f.followee_id = ? AND u.status != 'banned'
       ORDER BY f.created_at DESC LIMIT ? OFFSET ?`,
      req.user.id, req.params.id, limit, offset
    );
    res.json(paginated(rows.map((r) => publicUser(r, { is_following: !!r.is_following })), { limit, offset }));
  } catch (e) { next(e); }
});

usersRouter.get('/users/:id/following', requireAuth, (req, res, next) => {
  try {
    const { limit, offset } = pagination(req);
    const rows = all(
      `SELECT u.*, EXISTS(SELECT 1 FROM follows f WHERE f.follower_id = ? AND f.followee_id = u.id) AS is_following
       FROM follows f JOIN users u ON u.id = f.followee_id
       WHERE f.follower_id = ? AND u.status != 'banned'
       ORDER BY f.created_at DESC LIMIT ? OFFSET ?`,
      req.user.id, req.params.id, limit, offset
    );
    res.json(paginated(rows.map((r) => publicUser(r, { is_following: !!r.is_following })), { limit, offset }));
  } catch (e) { next(e); }
});

// "Who to follow": popular users not yet followed, with mutual-follow boost.
usersRouter.get('/suggestions/users', requireAuth, (req, res) => {
  const { limit } = pagination(req, 10, 50);
  const rows = all(
    `SELECT u.*, ${COUNTS},
       (SELECT COUNT(*) FROM follows mf
         WHERE mf.followee_id = u.id AND mf.follower_id IN
               (SELECT followee_id FROM follows WHERE follower_id = ?)) AS mutual_followers
     FROM users u
     WHERE u.id != ? AND u.status = 'active'
       AND NOT EXISTS (SELECT 1 FROM follows f WHERE f.follower_id = ? AND f.followee_id = u.id)
     ORDER BY mutual_followers DESC, follower_count DESC LIMIT ?`,
    req.user.id, req.user.id, req.user.id, limit
  );
  res.json({ data: rows.map((r) => publicUser(r, { follower_count: r.follower_count, mutual_followers: r.mutual_followers })) });
});

function shapePost(r) {
  return {
    id: r.id,
    content: r.content,
    media_url: r.media_url,
    created_at: r.created_at,
    author: { id: r.user_id, username: r.username, display_name: r.display_name, avatar_url: r.avatar_url },
    like_count: r.like_count,
    comment_count: r.comment_count,
    liked_by_me: !!r.liked_by_me,
  };
}
