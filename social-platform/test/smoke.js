// End-to-end smoke test. Starts the server on a scratch DB, exercises every feature area.
// Run: npm run smoke
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import assert from 'node:assert';

const PORT = 3999;
const BASE = `http://127.0.0.1:${PORT}`;
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'social-smoke-'));

const server = spawn(process.execPath, ['src/index.js'], {
  env: { ...process.env, PORT: String(PORT), DB_PATH: path.join(tmp, 'test.db'), JWT_SECRET: 'smoke-secret' },
  stdio: ['ignore', 'pipe', 'pipe'],
});
server.stderr.on('data', (d) => process.stderr.write(`[server:err] ${d}`));
server.stdout.on('data', (d) => process.stdout.write(`[server] ${d}`));
server.on('exit', (code) => { if (code) console.error(`[server exited with code ${code}]`); });

let failures = 0;
async function check(name, fn) {
  try {
    await fn();
    console.log(`  ok  ${name}`);
  } catch (e) {
    failures++;
    console.error(`FAIL  ${name}: ${e.message}`);
  }
}

async function api(method, path, { token, body } = {}) {
  const res = await fetch(BASE + path, {
    method,
    headers: {
      'content-type': 'application/json',
      ...(token ? { authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const json = await res.json().catch(() => ({}));
  return { status: res.status, json };
}

async function waitForServer() {
  for (let i = 0; i < 50; i++) {
    try {
      const res = await fetch(`${BASE}/health`);
      if (res.ok) return;
    } catch { /* not up yet */ }
    await new Promise((r) => setTimeout(r, 200));
  }
  throw new Error('server did not start');
}

const run = async () => {
  await waitForServer();
  let aliceToken, bobToken, adminToken, aliceId, bobId, postId, convoId;

  await check('health endpoint', async () => {
    const { status, json } = await api('GET', '/health');
    assert.equal(status, 200);
    assert.equal(json.status, 'ok');
  });

  await check('register two users', async () => {
    const a = await api('POST', '/api/auth/register', { body: { username: 'alice', email: 'alice@x.com', password: 'password123' } });
    assert.equal(a.status, 201);
    aliceToken = a.json.token; aliceId = a.json.user.id;
    const b = await api('POST', '/api/auth/register', { body: { username: 'bob', email: 'bob@x.com', password: 'password123' } });
    assert.equal(b.status, 201);
    bobToken = b.json.token; bobId = b.json.user.id;
  });

  await check('login', async () => {
    const { status, json } = await api('POST', '/api/auth/login', { body: { username: 'alice', password: 'password123' } });
    assert.equal(status, 200);
    assert.ok(json.token);
  });

  await check('rejects bad login', async () => {
    const { status } = await api('POST', '/api/auth/login', { body: { username: 'alice', password: 'wrong' } });
    assert.equal(status, 401);
  });

  await check('profile update + view', async () => {
    const p = await api('PATCH', '/api/me/profile', { token: aliceToken, body: { bio: 'hello there' } });
    assert.equal(p.status, 200);
    assert.equal(p.json.user.bio, 'hello there');
    const v = await api('GET', `/api/users/${bobId}`, { token: aliceToken });
    assert.equal(v.status, 200);
    assert.equal(v.json.user.username, 'bob');
  });

  await check('follow system + notification', async () => {
    const f = await api('POST', `/api/users/${bobId}/follow`, { token: aliceToken });
    assert.equal(f.status, 200);
    assert.equal(f.json.following, true);
    const n = await api('GET', '/api/notifications', { token: bobToken });
    assert.ok(n.json.data.some((x) => x.type === 'follow'));
    const list = await api('GET', `/api/users/${bobId}/followers`, { token: bobToken });
    assert.equal(list.json.data.length, 1);
  });

  await check('posts, likes, comments', async () => {
    const p = await api('POST', '/api/posts', { token: aliceToken, body: { content: 'smoke test post' } });
    assert.equal(p.status, 201);
    postId = p.json.post.id;
    const like = await api('POST', `/api/posts/${postId}/like`, { token: bobToken });
    assert.equal(like.json.like_count, 1);
    const c = await api('POST', `/api/posts/${postId}/comments`, { token: bobToken, body: { content: 'nice post' } });
    assert.equal(c.status, 201);
    const cl = await api('GET', `/api/posts/${postId}/comments`, { token: aliceToken });
    assert.equal(cl.json.data.length, 1);
  });

  await check('feed algorithm returns ranked posts', async () => {
    const feed = await api('GET', '/api/feed', { token: bobToken });
    assert.equal(feed.status, 200);
    assert.ok(feed.json.data.some((p) => p.id === postId));
    assert.ok(feed.json.data[0].score !== undefined);
    const explore = await api('GET', '/api/feed/explore', { token: bobToken });
    assert.equal(explore.status, 200);
  });

  await check('messaging', async () => {
    const c = await api('POST', '/api/conversations', { token: aliceToken, body: { user_id: bobId } });
    assert.equal(c.status, 201);
    convoId = c.json.conversation.id;
    const m = await api('POST', `/api/conversations/${convoId}/messages`, { token: aliceToken, body: { content: 'hey bob' } });
    assert.equal(m.status, 201);
    const history = await api('GET', `/api/conversations/${convoId}/messages`, { token: bobToken });
    assert.equal(history.json.data.length, 1);
    const list = await api('GET', '/api/conversations', { token: bobToken });
    assert.equal(list.json.data[0].unread_count, 1);
    await api('POST', `/api/conversations/${convoId}/read`, { token: bobToken });
  });

  await check('moderation: report, word filter, admin actions', async () => {
    const login = await api('POST', '/api/auth/login', { body: { username: 'admin', password: 'admin123' } });
    adminToken = login.json.token;
    assert.ok(adminToken, 'admin login');

    const r = await api('POST', '/api/reports', { token: bobToken, body: { target_type: 'post', target_id: postId, reason: 'spam' } });
    assert.equal(r.status, 201);
    const queue = await api('GET', '/api/moderation/reports', { token: adminToken });
    assert.ok(queue.json.data.length >= 1);

    const bad = await api('POST', '/api/posts', { token: aliceToken, body: { content: 'visit spamlink.example now' } });
    assert.equal(bad.status, 400);
    assert.equal(bad.json.error.code, 'content_flagged');

    const hide = await api('POST', '/api/moderation/hide', { token: adminToken, body: { target_type: 'post', target_id: postId } });
    assert.equal(hide.status, 200);
    const gone = await api('GET', `/api/posts/${postId}`, { token: bobToken });
    assert.equal(gone.status, 404);

    const mute = await api('POST', `/api/moderation/users/${bobId}/status`, { token: adminToken, body: { status: 'muted' } });
    assert.equal(mute.status, 200);
    const blocked = await api('POST', '/api/posts', { token: bobToken, body: { content: 'am I muted?' } });
    assert.equal(blocked.status, 403);
    await api('POST', `/api/moderation/users/${bobId}/status`, { token: adminToken, body: { status: 'active' } });
  });

  await check('analytics', async () => {
    const me = await api('GET', '/api/analytics/me', { token: aliceToken });
    assert.ok(me.json.posts >= 1);
    const postStats = await api('GET', `/api/analytics/posts/${postId}`, { token: aliceToken });
    assert.equal(postStats.status, 200);
    const overview = await api('GET', '/api/analytics/overview', { token: adminToken });
    assert.ok(overview.json.totals.users >= 2);
  });

  await check('unauthenticated requests are rejected', async () => {
    const { status } = await api('GET', '/api/feed');
    assert.equal(status, 401);
  });

  server.kill();
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(failures ? `\n${failures} check(s) FAILED` : '\nAll smoke checks passed');
  process.exit(failures ? 1 : 0);
};

run().catch((e) => {
  console.error(e);
  server.kill();
  process.exit(1);
});
