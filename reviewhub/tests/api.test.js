// Integration tests: real HTTP against a real (in-memory) database.
// Reasoning: no mocks. The review state machine and the merge gate are the
// product's correctness core — mocking the DB is exactly how such rules drift
// from reality. DB_PATH=:memory: gives every run a clean schema for free.
process.env.DB_PATH = ':memory:';

import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';

const { createApp } = await import('../server/index.js');

let server, base;
const tokens = {};

before(async () => {
  server = http.createServer(createApp());
  await new Promise(r => server.listen(0, r));
  base = `http://127.0.0.1:${server.address().port}/api`;

  // Fixture: owner alice, maintainer bob, member carol; one team, one repo.
  for (const u of ['alice', 'bob', 'carol', 'outsider']) {
    const r = await call('/auth/register', { method: 'POST', body: { username: u, email: `${u}@t.dev`, password: 'password123' } });
    assert.equal(r.status, 201);
    tokens[u] = r.data.token;
  }
  const team = await call('/teams', { method: 'POST', token: tokens.alice, body: { name: 'core' } });
  assert.equal(team.status, 201);
  globalThis.teamId = team.data.id;
  await call(`/teams/${teamId}/members`, { method: 'POST', token: tokens.alice, body: { username: 'bob', role: 'maintainer' } });
  await call(`/teams/${teamId}/members`, { method: 'POST', token: tokens.alice, body: { username: 'carol', role: 'member' } });
  const repo = await call(`/teams/${teamId}/repos`, { method: 'POST', token: tokens.alice, body: { name: 'api' } });
  globalThis.repoId = repo.data.id;
});
after(() => server.close());

async function call(path, { method = 'GET', token, body } = {}) {
  const res = await fetch(base + path, {
    method,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}) },
    body: body ? JSON.stringify(body) : undefined
  });
  return { status: res.status, data: await res.json().catch(() => ({})) };
}

const PATCH = `@@ -1,2 +1,3 @@
 line one
+added line
 line two`;

test('auth: register validates password length', async () => {
  const r = await call('/auth/register', { method: 'POST', body: { username: 'x', email: 'x@t.dev', password: 'short' } });
  assert.equal(r.status, 400);
});

test('auth: login rejects wrong password without revealing which part failed', async () => {
  const r = await call('/auth/login', { method: 'POST', body: { username: 'alice', password: 'wrongwrong' } });
  assert.equal(r.status, 401);
  assert.equal(r.data.error, 'invalid credentials');
});

test('auth: unauthenticated requests are rejected', async () => {
  const r = await call('/prs');
  assert.equal(r.status, 401);
});

test('teams: non-member cannot list repos', async () => {
  const r = await call(`/teams/${globalThis.teamId}/repos`, { token: tokens.outsider });
  assert.equal(r.status, 403);
});

test('prs: creation requires files and stores the patch', async () => {
  const bad = await call(`/repos/${globalThis.repoId}/prs`, { method: 'POST', token: tokens.carol, body: { title: 'x', files: [] } });
  assert.equal(bad.status, 400);
  const ok = await call(`/repos/${globalThis.repoId}/prs`, { method: 'POST', token: tokens.carol,
    body: { title: 'Add thing', files: [{ path: 'a.js', patch: PATCH }] } });
  assert.equal(ok.status, 201);
  globalThis.prId = ok.data.id;
  const detail = await call(`/prs/${globalThis.prId}`, { token: tokens.carol });
  assert.equal(detail.data.files.length, 1);
  assert.ok(detail.data.files[0].patch.includes('+added line'));
});

test('prs: outsider cannot read a team PR', async () => {
  const r = await call(`/prs/${globalThis.prId}`, { token: tokens.outsider });
  assert.equal(r.status, 403);
});

test('reviews: author cannot review own PR; teammate can', async () => {
  const self = await call(`/prs/${globalThis.prId}/reviews`, { method: 'POST', token: tokens.carol, body: { state: 'approved' } });
  assert.equal(self.status, 403);
  const other = await call(`/prs/${globalThis.prId}/reviews`, { method: 'POST', token: tokens.bob, body: { state: 'changes_requested', body: 'fix this' } });
  assert.equal(other.status, 201);
});

test('merge gate: blocked without approval; blocked with open change request', async () => {
  const r = await call(`/prs/${globalThis.prId}/status`, { method: 'POST', token: tokens.bob, body: { action: 'merge' } });
  assert.equal(r.status, 409);
  assert.ok(r.data.blockers.some(b => b.includes('change request')));
});

test('merge gate: member role cannot merge even with approval', async () => {
  await call(`/prs/${globalThis.prId}/reviews`, { method: 'POST', token: tokens.bob, body: { state: 'approved' } });
  const r = await call(`/prs/${globalThis.prId}/status`, { method: 'POST', token: tokens.carol, body: { action: 'merge' } });
  assert.equal(r.status, 403);
});

test('merge gate: maintainer merges after approval', async () => {
  const r = await call(`/prs/${globalThis.prId}/status`, { method: 'POST', token: tokens.bob, body: { action: 'merge' } });
  assert.equal(r.status, 200);
  assert.equal(r.data.status, 'merged');
  const again = await call(`/prs/${globalThis.prId}/status`, { method: 'POST', token: tokens.bob, body: { action: 'merge' } });
  assert.equal(again.status, 409, 'double merge must be rejected');
});

test('comments: inline comment must reference a file of the same PR', async () => {
  const pr2 = await call(`/repos/${globalThis.repoId}/prs`, { method: 'POST', token: tokens.alice,
    body: { title: 'second', files: [{ path: 'b.js', patch: PATCH }] } });
  const d1 = await call(`/prs/${globalThis.prId}`, { token: tokens.alice });
  const foreignFileId = d1.data.files[0].id;
  const r = await call(`/prs/${pr2.data.id}/comments`, { method: 'POST', token: tokens.alice,
    body: { body: 'cross-pr anchor', file_id: foreignFileId, line_number: 1 } });
  assert.equal(r.status, 400);
});

test('comments: author gets a notification when teammate comments', async () => {
  await call(`/prs/${globalThis.prId}/comments`, { method: 'POST', token: tokens.bob, body: { body: 'ping' } }).catch(() => {});
  // merged PR rejects comments, so use a fresh one
  const pr = await call(`/repos/${globalThis.repoId}/prs`, { method: 'POST', token: tokens.carol, body: { title: 'n', files: [{ path: 'n.js', patch: PATCH }] } });
  await call(`/prs/${pr.data.id}/comments`, { method: 'POST', token: tokens.bob, body: { body: 'hello author' } });
  const notifs = await call('/notifications', { token: tokens.carol });
  assert.ok(notifs.data.some(n => n.type === 'pr.comment'));
});

test('analytics: team member sees aggregates', async () => {
  const r = await call(`/teams/${globalThis.teamId}/analytics`, { token: tokens.carol });
  assert.equal(r.status, 200);
  assert.ok(r.data.totals.total >= 2);
  assert.ok(Array.isArray(r.data.reviewerLoad));
});

test('audit log records PR lifecycle', async () => {
  const r = await call(`/audit/pull_request/${globalThis.prId}`, { token: tokens.bob });
  const actions = r.data.map(a => a.action);
  assert.ok(actions.includes('pr.create'));
  assert.ok(actions.includes('pr.merge'));
});
