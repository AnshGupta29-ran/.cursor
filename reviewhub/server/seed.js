// Seed: demo data so the app is explorable in one command.
// All writes go through the same SQL the routes use — if seed works, the schema works.
import bcrypt from 'bcryptjs';
import { db, migrate } from './db.js';

migrate();

const hash = bcrypt.hashSync('password123', 10);
const insertUser = db.prepare('INSERT OR IGNORE INTO users (username, email, password_hash, display_name) VALUES (?,?,?,?)');
const alice = insertUser.run('alice', 'alice@example.com', hash, 'Alice (owner)');
const bob = insertUser.run('bob', 'bob@example.com', hash, 'Bob (maintainer)');
const carol = insertUser.run('carol', 'carol@example.com', hash, 'Carol (member)');
const uid = name => db.prepare('SELECT id FROM users WHERE username = ?').get(name).id;

db.prepare('INSERT OR IGNORE INTO teams (id, name, created_by) VALUES (1, ?, ?)').run('platform', uid('alice'));
const addMember = db.prepare('INSERT OR IGNORE INTO team_members (team_id, user_id, role) VALUES (1,?,?)');
addMember.run(uid('alice'), 'owner');
addMember.run(uid('bob'), 'maintainer');
addMember.run(uid('carol'), 'member');

db.prepare('INSERT OR IGNORE INTO repositories (id, team_id, provider, name, url) VALUES (1,1,?,?,?)')
  .run('manual', 'api-server', 'https://github.com/example/api-server');

const existing = db.prepare('SELECT id FROM pull_requests WHERE repo_id = 1 AND number = 1').get();
if (!existing) {
  const pr = db.prepare(`INSERT INTO pull_requests (repo_id, number, title, description, author_id, source_branch, target_branch)
                         VALUES (1,1,?,?,?,?,?)`)
    .run('Add rate limiting to /login',
         'Throttles repeated login attempts per IP to slow credential stuffing. 5 attempts per 60s window.',
         uid('carol'), 'feature/login-throttle', 'main');
  const prId = pr.lastInsertRowid;

  const patch = `diff --git a/src/auth.js b/src/auth.js
index 1111111..2222222 100644
--- a/src/auth.js
+++ b/src/auth.js
@@ -10,6 +10,12 @@ export function login(req, res) {
   const { username, password } = req.body;
+  const attempts = rateLimit.hit(clientIP(req));
+  if (attempts > 5) {
+    return res.status(429).json({ error: 'too many attempts, wait 60s' });
+  }
   const user = findUser(username);
   if (!user || !checkPassword(password, user.hash)) {
+    rateLimit.recordFailure(clientIP(req));
     return res.status(401).json({ error: 'invalid credentials' });
   }
+  rateLimit.reset(clientIP(req));
   return res.json({ token: issueToken(user) });
 }`;
  const file = db.prepare('INSERT INTO pr_files (pr_id, path, patch) VALUES (?,?,?)').run(prId, 'src/auth.js', patch);

  db.prepare('INSERT INTO comments (pr_id, file_id, line_number, author_id, body) VALUES (?,?,?,?,?)')
    .run(prId, file.lastInsertRowid, 13, uid('bob'), 'Should the limit be per-account as well as per-IP? Attackers rotate IPs.');
  db.prepare('INSERT INTO comments (pr_id, author_id, body) VALUES (?,?,?)')
    .run(prId, uid('alice'), 'Nice start. Please add a test for the 429 path before we merge.');

  db.prepare('INSERT INTO reviews (pr_id, reviewer_id, state, body) VALUES (?,?,?,?)')
    .run(prId, uid('bob'), 'changes_requested', 'Per-account limit + test, then good to go.');

  for (const item of ['Tests added for 429 path', 'Rate limit constant documented', 'No PII in rate-limit logs']) {
    db.prepare('INSERT INTO review_checklists (pr_id, item, checked) VALUES (?,?,?)').run(prId, item, item.includes('documented') ? 1 : 0);
  }

  // A second, already-merged PR so analytics have shape.
  const pr2 = db.prepare(`INSERT INTO pull_requests (repo_id, number, title, description, author_id, source_branch, target_branch, status)
                          VALUES (1,2,?,?,?,?,?,'merged')`)
    .run('Extract token issuance into auth/tokens.js', 'Pure refactor, no behavior change.', uid('alice'), 'refactor/tokens', 'main');
  db.prepare('INSERT INTO reviews (pr_id, reviewer_id, state, body) VALUES (?,?,?,?)')
    .run(pr2.lastInsertRowid, uid('bob'), 'approved', 'Clean split.');
}

console.log('Seeded. Logins: alice / bob / carol — password: password123');
