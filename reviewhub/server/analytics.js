import { Router } from 'express';
import { db } from './db.js';
import { requireTeamRole } from './auth.js';

// Four metrics chosen because each one predicts a specific review-health problem:
//  - median-ish time to first review  -> "reviews are stalling"
//  - approval rate                    -> "rubber-stamping vs real review"
//  - open PR age                      -> "WIP aging out, merge risk"
//  - reviewer load                    -> "bus factor on one senior"
// All are plain SQL aggregates — a nightly rollup table is the scaling answer,
// not a fancier query language.
export const analyticsRouter = Router();

analyticsRouter.get('/teams/:teamId/analytics', requireTeamRole('member'), (req, res) => {
  const teamId = Number(req.params.teamId);

  const totals = db.prepare(`
    SELECT COUNT(*) AS total,
           SUM(CASE WHEN p.status = 'open' THEN 1 ELSE 0 END) AS open,
           SUM(CASE WHEN p.status = 'merged' THEN 1 ELSE 0 END) AS merged,
           SUM(CASE WHEN p.status = 'closed' THEN 1 ELSE 0 END) AS closed
    FROM pull_requests p JOIN repositories r ON r.id = p.repo_id
    WHERE r.team_id = ?`).get(teamId);

  // Average hours from PR creation to that PR's first review.
  const timeToFirst = db.prepare(`
    SELECT AVG((julianday(first_at) - julianday(p.created_at)) * 24.0) AS avg_hours
    FROM pull_requests p
    JOIN repositories r ON r.id = p.repo_id
    JOIN (SELECT pr_id, MIN(created_at) AS first_at FROM reviews GROUP BY pr_id) f ON f.pr_id = p.id
    WHERE r.team_id = ?`).get(teamId);

  const reviewStates = db.prepare(`
    SELECT rv.state, COUNT(*) AS n FROM reviews rv
    JOIN pull_requests p ON p.id = rv.pr_id
    JOIN repositories r ON r.id = p.repo_id
    WHERE r.team_id = ? GROUP BY rv.state`).all(teamId);

  // Age in hours of each currently-open PR, oldest first — the stale-WIP list.
  const openAges = db.prepare(`
    SELECT p.id, p.number, p.title, r.name AS repo_name, u.username AS author_name,
           ROUND((julianday('now') - julianday(p.created_at)) * 24.0, 1) AS age_hours
    FROM pull_requests p
    JOIN repositories r ON r.id = p.repo_id
    JOIN users u ON u.id = p.author_id
    WHERE r.team_id = ? AND p.status = 'open'
    ORDER BY age_hours DESC LIMIT 10`).all(teamId);

  const reviewerLoad = db.prepare(`
    SELECT u.username, COUNT(*) AS reviews_done,
           SUM(CASE WHEN rv.state = 'changes_requested' THEN 1 ELSE 0 END) AS change_requests
    FROM reviews rv
    JOIN users u ON u.id = rv.reviewer_id
    JOIN pull_requests p ON p.id = rv.pr_id
    JOIN repositories r ON r.id = p.repo_id
    WHERE r.team_id = ? GROUP BY u.username ORDER BY reviews_done DESC`).all(teamId);

  res.json({ totals, avgHoursToFirstReview: timeToFirst.avg_hours, reviewStates, openAges, reviewerLoad });
});
