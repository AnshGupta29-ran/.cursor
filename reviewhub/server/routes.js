import { Router } from 'express';
import { db, audit } from './db.js';
import { requireAuth, requireTeamRole, teamRole, atLeast } from './auth.js';
import { emit } from './events.js';

export const api = Router();
api.use(requireAuth); // everything under /api requires a valid JWT

const getPR = id =>
  db.prepare(`SELECT p.*, r.team_id, r.name AS repo_name, u.username AS author_name
              FROM pull_requests p
              JOIN repositories r ON r.id = p.repo_id
              JOIN users u ON u.id = p.author_id
              WHERE p.id = ?`).get(id);

// The PR author counts as a reviewer of their own PR for nothing — authorization
// for any PR-scoped action is "author, or teammate of the owning repo".
function canAccessPR(userId, pr) {
  if (pr.author_id === userId) return true;
  return teamRole(userId, pr.team_id) !== null;
}

// ---------------- Teams ----------------

api.post('/teams', (req, res) => {
  const { name } = req.body || {};
  if (!name?.trim()) return res.status(400).json({ error: 'name is required' });
  if (db.prepare('SELECT id FROM teams WHERE name = ?').get(name.trim())) {
    return res.status(409).json({ error: 'team name already taken' });
  }
  // Team creation + creator-as-owner must be atomic — an ownerless team is an orphan.
  const tx = db.transaction(() => {
    const t = db.prepare('INSERT INTO teams (name, created_by) VALUES (?,?)').run(name.trim(), req.user.id);
    db.prepare('INSERT INTO team_members (team_id, user_id, role) VALUES (?,?,?)').run(t.lastInsertRowid, req.user.id, 'owner');
    return t.lastInsertRowid;
  });
  const id = tx();
  audit(req.user.id, 'team.create', 'team', id, { name });
  res.status(201).json({ id, name: name.trim() });
});

api.get('/teams', (req, res) => {
  res.json(db.prepare(`SELECT t.id, t.name, m.role FROM teams t
                       JOIN team_members m ON m.team_id = t.id
                       WHERE m.user_id = ? ORDER BY t.name`).all(req.user.id));
});

api.post('/teams/:teamId/members', requireTeamRole('owner'), (req, res) => {
  const { username, role } = req.body || {};
  if (!['member', 'maintainer'].includes(role)) return res.status(400).json({ error: 'role must be member or maintainer' });
  const user = db.prepare('SELECT id FROM users WHERE username = ?').get(username || '');
  if (!user) return res.status(404).json({ error: 'no such user' });
  db.prepare(`INSERT INTO team_members (team_id, user_id, role) VALUES (?,?,?)
              ON CONFLICT (team_id, user_id) DO UPDATE SET role = excluded.role`)
    .run(Number(req.params.teamId), user.id, role);
  audit(req.user.id, 'team.member.add', 'team', req.params.teamId, { username, role });
  res.status(201).json({ ok: true });
});

// ---------------- Repositories ----------------

api.post('/teams/:teamId/repos', requireTeamRole('maintainer'), (req, res) => {
  const { name, provider, url } = req.body || {};
  if (!name?.trim()) return res.status(400).json({ error: 'name is required' });
  try {
    const info = db.prepare('INSERT INTO repositories (team_id, provider, name, url) VALUES (?,?,?,?)')
      .run(Number(req.params.teamId), provider || 'manual', name.trim(), url || '');
    audit(req.user.id, 'repo.create', 'repository', info.lastInsertRowid, { name });
    res.status(201).json({ id: info.lastInsertRowid });
  } catch {
    res.status(409).json({ error: 'repo already exists in this team' });
  }
});

api.get('/teams/:teamId/repos', requireTeamRole('member'), (req, res) => {
  res.json(db.prepare('SELECT id, name, provider, url, default_branch FROM repositories WHERE team_id = ? ORDER BY name')
    .all(Number(req.params.teamId)));
});

// ---------------- Pull Requests ----------------

api.get('/prs', (req, res) => {
  // "My reviews": PRs in my teams where I'm not the author, plus my own open ones.
  // Status filter keeps dashboards actionable; filters are query params, never stored state.
  const status = ['open', 'merged', 'closed'].includes(req.query.status) ? req.query.status : 'open';
  res.json(db.prepare(`
    SELECT p.id, p.number, p.title, p.status, p.created_at, r.name AS repo_name, u.username AS author_name,
      (SELECT state FROM reviews rv WHERE rv.pr_id = p.id AND rv.reviewer_id = ?) AS my_review
    FROM pull_requests p
    JOIN repositories r ON r.id = p.repo_id
    JOIN team_members m ON m.team_id = r.team_id
    JOIN users u ON u.id = p.author_id
    WHERE m.user_id = ? AND p.status = ?
    ORDER BY p.updated_at DESC`).all(req.user.id, req.user.id, status));
});

api.post('/repos/:repoId/prs', (req, res) => {
  const repo = db.prepare('SELECT * FROM repositories WHERE id = ?').get(Number(req.params.repoId));
  if (!repo) return res.status(404).json({ error: 'repo not found' });
  if (!teamRole(req.user.id, repo.team_id)) return res.status(403).json({ error: 'not a team member' });

  const { title, description, source_branch, target_branch, files } = req.body || {};
  if (!title?.trim()) return res.status(400).json({ error: 'title is required' });
  if (!Array.isArray(files) || files.length === 0) {
    return res.status(400).json({ error: 'at least one changed file with a unified-diff patch is required' });
  }

  // PR + its files + the next per-repo number must be atomic — a half-created
  // PR would render a diff-less review page. db.transaction gives us that.
  const tx = db.transaction(() => {
    const next = (db.prepare('SELECT COALESCE(MAX(number),0)+1 AS n FROM pull_requests WHERE repo_id = ?').get(repo.id)).n;
    const info = db.prepare(`INSERT INTO pull_requests (repo_id, number, title, description, author_id, source_branch, target_branch)
                             VALUES (?,?,?,?,?,?,?)`)
      .run(repo.id, next, title.trim(), description || '', req.user.id,
           source_branch || 'feature', target_branch || repo.default_branch);
    const insertFile = db.prepare('INSERT INTO pr_files (pr_id, path, patch) VALUES (?,?,?)');
    for (const f of files) {
      if (!f.path || typeof f.patch !== 'string') throw new Error('each file needs path and patch');
      insertFile.run(info.lastInsertRowid, String(f.path).slice(0, 500), f.patch.slice(0, 200_000));
    }
    return info.lastInsertRowid;
  });

  try {
    const prId = tx();
    audit(req.user.id, 'pr.create', 'pull_request', prId, { repo: repo.name });
    const pr = getPR(prId);
    emit('pr.created', { pr, actor: req.user });
    res.status(201).json({ id: prId, number: pr.number });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

api.get('/prs/:id', (req, res) => {
  const pr = getPR(Number(req.params.id));
  if (!pr) return res.status(404).json({ error: 'PR not found' });
  if (!canAccessPR(req.user.id, pr)) return res.status(403).json({ error: 'no access' });

  const files = db.prepare('SELECT id, path, patch FROM pr_files WHERE pr_id = ? ORDER BY path').all(pr.id);
  const comments = db.prepare(`SELECT c.*, u.username AS author_name FROM comments c
                               JOIN users u ON u.id = c.author_id
                               WHERE c.pr_id = ? ORDER BY c.created_at, c.id`).all(pr.id);
  const reviews = db.prepare(`SELECT rv.*, u.username AS reviewer_name FROM reviews rv
                              JOIN users u ON u.id = rv.reviewer_id WHERE rv.pr_id = ?`).all(pr.id);
  const checklist = db.prepare('SELECT id, item, checked FROM review_checklists WHERE pr_id = ?').all(pr.id);
  const role = teamRole(req.user.id, pr.team_id);
  res.json({
    pr, files, comments, reviews, checklist,
    viewer: { userId: req.user.id, isAuthor: pr.author_id === req.user.id, role, canMerge: atLeast(role, 'maintainer') }
  });
});

api.post('/prs/:id/status', (req, res) => {
  const pr = getPR(Number(req.params.id));
  if (!pr) return res.status(404).json({ error: 'PR not found' });
  if (!canAccessPR(req.user.id, pr)) return res.status(403).json({ error: 'no access' });
  const { action } = req.body || {};

  const setStatus = s => db.prepare("UPDATE pull_requests SET status = ?, updated_at = datetime('now') WHERE id = ?").run(s, pr.id);

  if (action === 'merge') {
    // The merge gate is enforced here and only here — the UI hides the button,
    // but the server is the authority. All three conditions, or 409.
    if (!atLeast(teamRole(req.user.id, pr.team_id), 'maintainer')) {
      return res.status(403).json({ error: 'only maintainers and owners can merge' });
    }
    if (pr.status !== 'open') return res.status(409).json({ error: 'PR is not open' });
    const blockers = [];
    if (!db.prepare("SELECT 1 FROM reviews WHERE pr_id = ? AND state = 'approved'").get(pr.id)) {
      blockers.push('at least one approval is required');
    }
    if (db.prepare("SELECT 1 FROM reviews WHERE pr_id = ? AND state = 'changes_requested'").get(pr.id)) {
      blockers.push('unresolved change requests exist');
    }
    if (blockers.length) return res.status(409).json({ error: 'merge blocked', blockers });
    setStatus('merged');
  } else if (action === 'close') {
    if (!(req.user.id === pr.author_id || atLeast(teamRole(req.user.id, pr.team_id), 'maintainer'))) {
      return res.status(403).json({ error: 'only the author or a maintainer can close' });
    }
    if (pr.status !== 'open') return res.status(409).json({ error: 'PR is not open' });
    setStatus('closed');
  } else if (action === 'reopen') {
    if (!(req.user.id === pr.author_id || atLeast(teamRole(req.user.id, pr.team_id), 'maintainer'))) {
      return res.status(403).json({ error: 'only the author or a maintainer can reopen' });
    }
    if (pr.status === 'open') return res.status(409).json({ error: 'PR is already open' });
    setStatus('open');
  } else {
    return res.status(400).json({ error: 'action must be merge, close or reopen' });
  }

  const updated = getPR(pr.id);
  audit(req.user.id, `pr.${action}`, 'pull_request', pr.id);
  emit('pr.status', { pr: updated, actor: req.user });
  res.json({ status: updated.status });
});

// ---------------- Comments ----------------

api.post('/prs/:id/comments', (req, res) => {
  const pr = getPR(Number(req.params.id));
  if (!pr) return res.status(404).json({ error: 'PR not found' });
  if (!canAccessPR(req.user.id, pr)) return res.status(403).json({ error: 'no access' });
  if (pr.status === 'merged') return res.status(409).json({ error: 'cannot comment on a merged PR' });

  const { body, file_id, line_number, parent_id } = req.body || {};
  if (!body?.trim()) return res.status(400).json({ error: 'body is required' });

  // Inline comments must reference a file that actually belongs to this PR —
  // otherwise a crafted request could anchor a comment to another PR's file.
  if (file_id != null) {
    const f = db.prepare('SELECT id FROM pr_files WHERE id = ? AND pr_id = ?').get(Number(file_id), pr.id);
    if (!f) return res.status(400).json({ error: 'file does not belong to this PR' });
  }
  if (parent_id != null) {
    const p = db.prepare('SELECT id FROM comments WHERE id = ? AND pr_id = ?').get(Number(parent_id), pr.id);
    if (!p) return res.status(400).json({ error: 'parent comment does not belong to this PR' });
  }

  const info = db.prepare('INSERT INTO comments (pr_id, file_id, line_number, parent_id, author_id, body) VALUES (?,?,?,?,?,?)')
    .run(pr.id, file_id ?? null, line_number ?? null, parent_id ?? null, req.user.id, body.trim());
  audit(req.user.id, 'comment.create', 'comment', info.lastInsertRowid, { prId: pr.id });
  const comment = db.prepare('SELECT * FROM comments WHERE id = ?').get(info.lastInsertRowid);
  emit('pr.comment', { pr, comment, actor: req.user });
  res.status(201).json({ id: info.lastInsertRowid });
});

api.post('/comments/:id/resolve', (req, res) => {
  const comment = db.prepare('SELECT * FROM comments WHERE id = ?').get(Number(req.params.id));
  if (!comment) return res.status(404).json({ error: 'comment not found' });
  const pr = getPR(comment.pr_id);
  // Resolution is trusted to the thread participants: comment author, PR author,
  // or a maintainer. Anyone else would be able to silently bury feedback.
  const allowed = comment.author_id === req.user.id || pr.author_id === req.user.id ||
    atLeast(teamRole(req.user.id, pr.team_id), 'maintainer');
  if (!allowed) return res.status(403).json({ error: 'cannot resolve this thread' });
  db.prepare('UPDATE comments SET resolved = 1 - resolved WHERE id = ?').run(comment.id);
  emit('pr.comment', { pr, comment, actor: req.user });
  res.json({ resolved: !comment.resolved });
});

// ---------------- Reviews ----------------

api.post('/prs/:id/reviews', (req, res) => {
  const pr = getPR(Number(req.params.id));
  if (!pr) return res.status(404).json({ error: 'PR not found' });
  if (!teamRole(req.user.id, pr.team_id)) return res.status(403).json({ error: 'not a team member' });
  // Self-approval is meaningless — the rule that makes "approved" a signal.
  if (pr.author_id === req.user.id) return res.status(403).json({ error: 'authors cannot review their own PR' });
  if (pr.status !== 'open') return res.status(409).json({ error: 'PR is not open' });

  const { state, body } = req.body || {};
  if (!['approved', 'changes_requested', 'commented'].includes(state)) {
    return res.status(400).json({ error: 'state must be approved, changes_requested or commented' });
  }
  // UPSERT: the latest verdict per reviewer replaces the old one, so an
  // author who fixes issues earns a clean "changes_requested -> approved" flip.
  db.prepare(`INSERT INTO reviews (pr_id, reviewer_id, state, body) VALUES (?,?,?,?)
              ON CONFLICT (pr_id, reviewer_id) DO UPDATE SET state = excluded.state, body = excluded.body`)
    .run(pr.id, req.user.id, state, body || '');
  audit(req.user.id, `review.${state}`, 'pull_request', pr.id);
  const review = db.prepare('SELECT * FROM reviews WHERE pr_id = ? AND reviewer_id = ?').get(pr.id, req.user.id);
  emit('pr.review', { pr, review, actor: req.user });
  res.status(201).json({ ok: true });
});

// ---------------- Checklist ----------------

api.post('/prs/:id/checklist', (req, res) => {
  const pr = getPR(Number(req.params.id));
  if (!pr || !canAccessPR(req.user.id, pr)) return res.status(pr ? 403 : 404).json({ error: 'not found or no access' });
  const { item } = req.body || {};
  if (!item?.trim()) return res.status(400).json({ error: 'item is required' });
  const info = db.prepare('INSERT INTO review_checklists (pr_id, item) VALUES (?,?)').run(pr.id, item.trim());
  emit('pr.checklist', { pr });
  res.status(201).json({ id: info.lastInsertRowid });
});

api.post('/checklist/:id/toggle', (req, res) => {
  const item = db.prepare('SELECT * FROM review_checklists WHERE id = ?').get(Number(req.params.id));
  if (!item) return res.status(404).json({ error: 'item not found' });
  const pr = getPR(item.pr_id);
  if (!canAccessPR(req.user.id, pr)) return res.status(403).json({ error: 'no access' });
  db.prepare('UPDATE review_checklists SET checked = 1 - checked WHERE id = ?').run(item.id);
  emit('pr.checklist', { pr });
  res.json({ checked: !item.checked });
});

// ---------------- Notifications ----------------

api.get('/notifications', (req, res) => {
  res.json(db.prepare('SELECT * FROM notifications WHERE user_id = ? ORDER BY id DESC LIMIT 50').all(req.user.id));
});

api.post('/notifications/read', (req, res) => {
  db.prepare('UPDATE notifications SET read = 1 WHERE user_id = ?').run(req.user.id);
  res.json({ ok: true });
});

api.get('/audit/:entity/:id', (req, res) => {
  res.json(db.prepare(`SELECT a.*, u.username FROM audit_log a LEFT JOIN users u ON u.id = a.user_id
                       WHERE a.entity = ? AND a.entity_id = ? ORDER BY a.id DESC LIMIT 100`)
    .all(req.params.entity, Number(req.params.id)));
});
