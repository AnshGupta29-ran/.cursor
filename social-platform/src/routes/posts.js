import { Router } from 'express';
import { all, get, run } from '../db.js';
import { requireAuth, requireNotMuted } from '../auth/middleware.js';
import { badRequest, forbidden, notFound, pagination, paginated, extractMentions } from '../utils/http.js';
import { track } from '../utils/analytics.js';
import { notify } from '../utils/notify.js';
import { scanText } from '../utils/moderation.js';

export const postsRouter = Router();

const POST_SELECT = `
  SELECT p.id, p.user_id, p.content, p.media_url, p.created_at,
         u.username, u.display_name, u.avatar_url, u.status AS author_status,
         (SELECT COUNT(*) FROM likes l WHERE l.post_id = p.id) AS like_count,
         (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id AND c.hidden = 0) AS comment_count
  FROM posts p JOIN users u ON u.id = p.user_id
`;

function shapePost(r, liked = 0) {
  return {
    id: r.id,
    content: r.content,
    media_url: r.media_url,
    created_at: r.created_at,
    author: { id: r.user_id, username: r.username, display_name: r.display_name, avatar_url: r.avatar_url },
    like_count: r.like_count,
    comment_count: r.comment_count,
    liked_by_me: !!liked,
  };
}

function notifyMentions(content, actorId, entityId) {
  for (const name of extractMentions(content)) {
    const target = get('SELECT id FROM users WHERE username = ? AND status = \'active\'', name);
    if (target) notify(target.id, actorId, 'mention', entityId);
  }
}

postsRouter.post('/posts', requireAuth, requireNotMuted, (req, res, next) => {
  try {
    const { content, media_url } = req.body || {};
    const text = String(content || '').trim();
    if (!text) throw badRequest('content is required');
    if (text.length > 5000) throw badRequest('content too long (max 5000 chars)');
    if (media_url && String(media_url).length > 500) throw badRequest('media_url too long');

    // Content moderation: reject prohibited content outright.
    const scan = scanText(text);
    if (!scan.ok) throw badRequest(`Post rejected by content filter (${scan.matches.join(', ')})`, 'content_flagged');

    const info = run('INSERT INTO posts (user_id, content, media_url) VALUES (?,?,?)', req.user.id, text, String(media_url || ''));
    const postId = Number(info.lastInsertRowid);
    track('post_create', { userId: req.user.id, entityType: 'post', entityId: postId });
    notifyMentions(text, req.user.id, postId);

    const row = get(`${POST_SELECT} WHERE p.id = ?`, postId);
    res.status(201).json({ post: shapePost(row) });
  } catch (e) { next(e); }
});

postsRouter.get('/posts/:id', requireAuth, (req, res, next) => {
  try {
    const row = get(`${POST_SELECT} WHERE p.id = ? AND p.hidden = 0`, req.params.id);
    if (!row || row.author_status === 'banned') throw notFound('Post not found');
    const liked = get('SELECT 1 FROM likes WHERE user_id = ? AND post_id = ?', req.user.id, row.id);
    track('post_view', { userId: req.user.id, entityType: 'post', entityId: row.id });
    res.json({ post: shapePost(row, liked) });
  } catch (e) { next(e); }
});

postsRouter.delete('/posts/:id', requireAuth, (req, res, next) => {
  try {
    const post = get('SELECT user_id FROM posts WHERE id = ?', req.params.id);
    if (!post) throw notFound('Post not found');
    if (post.user_id !== req.user.id && req.user.role !== 'admin') throw forbidden('You can only delete your own posts');
    run('DELETE FROM posts WHERE id = ?', req.params.id);
    res.json({ ok: true });
  } catch (e) { next(e); }
});

// ---- Likes ----

postsRouter.post('/posts/:id/like', requireAuth, requireNotMuted, (req, res, next) => {
  try {
    const post = get('SELECT id, user_id FROM posts WHERE id = ? AND hidden = 0', req.params.id);
    if (!post) throw notFound('Post not found');
    const existing = get('SELECT 1 FROM likes WHERE user_id = ? AND post_id = ?', req.user.id, post.id);
    if (!existing) {
      run('INSERT INTO likes (user_id, post_id) VALUES (?,?)', req.user.id, post.id);
      track('like', { userId: req.user.id, entityType: 'post', entityId: post.id });
      notify(post.user_id, req.user.id, 'like', post.id);
    }
    const { c } = get('SELECT COUNT(*) AS c FROM likes WHERE post_id = ?', post.id);
    res.json({ liked: true, like_count: c });
  } catch (e) { next(e); }
});

postsRouter.delete('/posts/:id/like', requireAuth, (req, res, next) => {
  try {
    run('DELETE FROM likes WHERE user_id = ? AND post_id = ?', req.user.id, req.params.id);
    const { c } = get('SELECT COUNT(*) AS c FROM likes WHERE post_id = ?', req.params.id);
    res.json({ liked: false, like_count: c });
  } catch (e) { next(e); }
});

// ---- Comments (threaded) ----

postsRouter.post('/posts/:id/comments', requireAuth, requireNotMuted, (req, res, next) => {
  try {
    const post = get('SELECT id, user_id FROM posts WHERE id = ? AND hidden = 0', req.params.id);
    if (!post) throw notFound('Post not found');
    const { content, parent_id } = req.body || {};
    const text = String(content || '').trim();
    if (!text) throw badRequest('content is required');
    if (text.length > 2000) throw badRequest('content too long (max 2000 chars)');

    let parent = null;
    if (parent_id != null) {
      parent = get('SELECT id, user_id, post_id FROM comments WHERE id = ? AND hidden = 0', parent_id);
      if (!parent || parent.post_id !== post.id) throw badRequest('parent_id does not belong to this post');
    }

    const scan = scanText(text);
    if (!scan.ok) throw badRequest(`Comment rejected by content filter (${scan.matches.join(', ')})`, 'content_flagged');

    const info = run('INSERT INTO comments (post_id, user_id, parent_id, content) VALUES (?,?,?,?)', post.id, req.user.id, parent?.id ?? null, text);
    const commentId = Number(info.lastInsertRowid);
    track('comment_create', { userId: req.user.id, entityType: 'post', entityId: post.id });
    notify(post.user_id, req.user.id, 'comment', post.id);
    if (parent) notify(parent.user_id, req.user.id, 'comment', post.id);
    notifyMentions(text, req.user.id, post.id);

    const row = get(
      `SELECT c.*, u.username, u.display_name, u.avatar_url FROM comments c JOIN users u ON u.id = c.user_id WHERE c.id = ?`,
      commentId
    );
    res.status(201).json({ comment: shapeComment(row) });
  } catch (e) { next(e); }
});

postsRouter.get('/posts/:id/comments', requireAuth, (req, res, next) => {
  try {
    const post = get('SELECT id FROM posts WHERE id = ? AND hidden = 0', req.params.id);
    if (!post) throw notFound('Post not found');
    const { limit, offset } = pagination(req, 50);
    const rows = all(
      `SELECT c.*, u.username, u.display_name, u.avatar_url
       FROM comments c JOIN users u ON u.id = c.user_id
       WHERE c.post_id = ? AND c.hidden = 0 AND u.status != 'banned'
       ORDER BY c.created_at ASC, c.id ASC LIMIT ? OFFSET ?`,
      post.id, limit, offset
    );
    // Build a two-level tree client-side-friendly: top-level comments carry their replies inline.
    const byId = new Map();
    const roots = [];
    for (const r of rows) {
      const c = shapeComment(r);
      c.replies = [];
      byId.set(c.id, c);
      if (c.parent_id && byId.has(c.parent_id)) byId.get(c.parent_id).replies.push(c);
      else if (c.parent_id) roots.push(c); // parent outside this page — return flat
      else roots.push(c);
    }
    res.json(paginated(roots, { limit, offset }));
  } catch (e) { next(e); }
});

postsRouter.delete('/comments/:id', requireAuth, (req, res, next) => {
  try {
    const comment = get('SELECT user_id FROM comments WHERE id = ?', req.params.id);
    if (!comment) throw notFound('Comment not found');
    if (comment.user_id !== req.user.id && req.user.role !== 'admin') throw forbidden('You can only delete your own comments');
    run('DELETE FROM comments WHERE id = ?', req.params.id);
    res.json({ ok: true });
  } catch (e) { next(e); }
});

function shapeComment(r) {
  return {
    id: r.id,
    post_id: r.post_id,
    parent_id: r.parent_id,
    content: r.content,
    created_at: r.created_at,
    author: { id: r.user_id, username: r.username, display_name: r.display_name, avatar_url: r.avatar_url },
  };
}
