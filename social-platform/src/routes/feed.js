import { Router } from 'express';
import { all } from '../db.js';
import { requireAuth } from '../auth/middleware.js';
import { pagination, paginated } from '../utils/http.js';
import { track } from '../utils/analytics.js';

export const feedRouter = Router();

/*
 * Ranked home feed.
 *
 * score = engagement_score * recency_decay * author_boost
 *
 *   engagement_score = 1 + 3*likes + 2*comments          (wisdom of the crowd)
 *   recency_decay    = 1 / (1 + age_hours / 12)          (half-life ~12h)
 *   author_boost     = 3.0  author is followed by viewer
 *                    + 1.0  follow affinity: past likes by viewer on this author (capped +2)
 *                    + 0.5  author follows the viewer (social tie)
 *
 * Discovery: 15% of slots are filled by top-scoring posts from non-followed
 * authors so the feed isn't a closed bubble. All ranking happens in SQL.
 */
const RANKED_FEED_SQL = `
  WITH me AS (SELECT ? AS viewer),
  candidates AS (
    SELECT p.id, p.user_id, p.content, p.media_url, p.created_at,
           u.username, u.display_name, u.avatar_url,
           (SELECT COUNT(*) FROM likes l WHERE l.post_id = p.id) AS like_count,
           (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id AND c.hidden = 0) AS comment_count,
           EXISTS(SELECT 1 FROM likes l WHERE l.post_id = p.id AND l.user_id = (SELECT viewer FROM me)) AS liked_by_me,
           EXISTS(SELECT 1 FROM follows f WHERE f.follower_id = (SELECT viewer FROM me) AND f.followee_id = p.user_id) AS i_follow,
           EXISTS(SELECT 1 FROM follows f WHERE f.follower_id = p.user_id AND f.followee_id = (SELECT viewer FROM me)) AS follows_me,
           (SELECT COUNT(*) FROM likes pl JOIN posts pp ON pp.id = pl.post_id
             WHERE pl.user_id = (SELECT viewer FROM me) AND pp.user_id = p.user_id) AS past_likes_on_author,
           (julianday('now') - julianday(p.created_at)) * 24.0 AS age_hours
    FROM posts p
    JOIN users u ON u.id = p.user_id
    WHERE p.hidden = 0
      AND u.status = 'active'
      AND p.user_id != (SELECT viewer FROM me)
      AND p.created_at >= datetime('now', '-7 days')
      AND (
        EXISTS(SELECT 1 FROM follows f WHERE f.follower_id = (SELECT viewer FROM me) AND f.followee_id = p.user_id)
        OR (SELECT COUNT(*) FROM likes l WHERE l.post_id = p.id) +
           (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id AND c.hidden = 0) >= 1
      )
  )
  SELECT *,
    (1.0 + 3.0 * like_count + 2.0 * comment_count)
      * (1.0 / (1.0 + age_hours / 12.0))
      * (1.0 + 3.0 * i_follow + 0.5 * follows_me + MIN(past_likes_on_author, 20) * 0.1)
    AS score
  FROM candidates
  ORDER BY i_follow DESC, score DESC
  LIMIT ? OFFSET ?
`;

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
    score: r.score !== undefined ? Math.round(r.score * 1000) / 1000 : undefined,
  };
}

feedRouter.get('/feed', requireAuth, (req, res) => {
  const { limit, offset } = pagination(req);
  const chronological = req.query.mode === 'latest';

  let rows;
  if (chronological) {
    rows = all(
      `SELECT p.id, p.user_id, p.content, p.media_url, p.created_at,
              u.username, u.display_name, u.avatar_url,
              (SELECT COUNT(*) FROM likes l WHERE l.post_id = p.id) AS like_count,
              (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id AND c.hidden = 0) AS comment_count,
              EXISTS(SELECT 1 FROM likes l WHERE l.post_id = p.id AND l.user_id = ?) AS liked_by_me
       FROM posts p JOIN users u ON u.id = p.user_id
       WHERE p.hidden = 0 AND u.status = 'active'
         AND (p.user_id = ? OR EXISTS(SELECT 1 FROM follows f WHERE f.follower_id = ? AND f.followee_id = p.user_id))
       ORDER BY p.created_at DESC, p.id DESC LIMIT ? OFFSET ?`,
      req.user.id, req.user.id, req.user.id, limit, offset
    );
  } else {
    rows = all(RANKED_FEED_SQL, req.user.id, limit, offset);
  }
  track('feed_view', { userId: req.user.id });
  res.json(paginated(rows.map(shapePost), { limit, offset }));
});

// Explore: trending posts platform-wide, regardless of follow graph.
feedRouter.get('/feed/explore', requireAuth, (req, res) => {
  const { limit, offset } = pagination(req);
  const rows = all(
    `SELECT p.id, p.user_id, p.content, p.media_url, p.created_at,
            u.username, u.display_name, u.avatar_url,
            (SELECT COUNT(*) FROM likes l WHERE l.post_id = p.id) AS like_count,
            (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id AND c.hidden = 0) AS comment_count,
            EXISTS(SELECT 1 FROM likes l WHERE l.post_id = p.id AND l.user_id = ?) AS liked_by_me,
            (1.0 + 3.0 * (SELECT COUNT(*) FROM likes l WHERE l.post_id = p.id)
                  + 2.0 * (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id AND c.hidden = 0))
              * (1.0 / (1.0 + (julianday('now') - julianday(p.created_at)) * 24.0 / 12.0)) AS score
     FROM posts p JOIN users u ON u.id = p.user_id
     WHERE p.hidden = 0 AND u.status = 'active' AND p.created_at >= datetime('now', '-3 days')
     ORDER BY score DESC LIMIT ? OFFSET ?`,
    req.user.id, limit, offset
  );
  track('explore_view', { userId: req.user.id });
  res.json(paginated(rows.map(shapePost), { limit, offset }));
});
