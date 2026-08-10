const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { WebSocketServer } = require('ws');

// Prefer ws if installed; otherwise fall back to no-WS mode after load attempt
let WSS = null;
try {
  WSS = require('ws').WebSocketServer;
} catch {
  WSS = null;
}

const PORT = process.env.PORT || 5050;
const ROOT = path.join(__dirname, '..');
const users = new Map();
const scores = [];
const tokens = new Map();

function uuid() {
  return crypto.randomUUID();
}

function sendJson(res, status, body) {
  const data = JSON.stringify(body);
  res.writeHead(status, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
  });
  res.end(data);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let raw = '';
    req.on('data', (c) => (raw += c));
    req.on('end', () => {
      if (!raw) return resolve({});
      try { resolve(JSON.parse(raw)); } catch (e) { reject(e); }
    });
  });
}

function contentType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  return ({
    '.html': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json',
    '.md': 'text/markdown; charset=utf-8',
  })[ext] || 'application/octet-stream';
}

async function handleApi(req, res, url) {
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    });
    return res.end();
  }

  if (url.pathname === '/api/health') return sendJson(res, 200, { ok: true, service: 'gaming-platform' });

  if (url.pathname === '/api/auth/register' && req.method === 'POST') {
    const body = await readBody(req);
    if (!body.username || !body.password) return sendJson(res, 400, { error: 'username/password required' });
    if (users.has(body.username)) return sendJson(res, 409, { error: 'user exists' });
    const user = { id: uuid(), username: body.username, password: body.password };
    users.set(user.username, user);
    return sendJson(res, 200, { id: user.id, username: user.username });
  }

  if (url.pathname === '/api/auth/login' && req.method === 'POST') {
    const body = await readBody(req);
    let user = users.get(body.username);
    if (!user) {
      user = { id: uuid(), username: body.username || 'guest', password: body.password || 'demo' };
      users.set(user.username, user);
    } else if (user.password !== body.password) {
      return sendJson(res, 401, { error: 'invalid credentials' });
    }
    const token = uuid();
    tokens.set(token, user.username);
    return sendJson(res, 200, { token, user: { id: user.id, username: user.username } });
  }

  if (url.pathname === '/api/auth/profile' && req.method === 'GET') {
    const auth = req.headers.authorization || '';
    const token = auth.replace(/^Bearer\s+/i, '');
    const username = tokens.get(token);
    if (!username) return sendJson(res, 401, { error: 'unauthorized' });
    const user = users.get(username);
    return sendJson(res, 200, { id: user.id, username: user.username });
  }

  if (url.pathname === '/api/games') {
    return sendJson(res, 200, [{ id: 'demo-game', name: 'Orb Collector', description: 'Collect orbs with the engine demo' }]);
  }

  if (url.pathname === '/api/scores/record' && req.method === 'POST') {
    const body = await readBody(req);
    const username = body.username || 'player1';
    const entry = {
      id: uuid(),
      userId: users.get(username)?.id || uuid(),
      username,
      gameId: body.gameId || 'demo-game',
      points: Number(body.points) || 0,
      playedAt: new Date().toISOString(),
    };
    scores.push(entry);
    return sendJson(res, 200, entry);
  }

  if (url.pathname.startsWith('/api/scores/user/')) {
    const id = url.pathname.split('/').pop();
    return sendJson(res, 200, scores.filter((s) => s.userId === id || s.username === id));
  }

  if (url.pathname.startsWith('/api/leaderboards/')) {
    const gameId = url.pathname.split('/').pop();
    const ranking = scores
      .filter((s) => s.gameId === gameId)
      .sort((a, b) => b.points - a.points)
      .slice(0, 20)
      .map((s, i) => ({ rank: i + 1, username: s.username, points: s.points, playedAt: s.playedAt }));
    return sendJson(res, 200, { gameId, ranking });
  }

  return sendJson(res, 404, { error: 'not found' });
}

function serveStatic(req, res, urlPath) {
  let rel = decodeURIComponent(urlPath);
  if (rel === '/' || rel === '') rel = '/index.html';
  // Map site root files from /public, keep /engine as-is
  if (rel.startsWith('/engine/')) {
    rel = rel.slice(1);
  } else {
    rel = path.join('public', rel.replace(/^\/+/, ''));
  }
  const filePath = path.normalize(path.join(ROOT, rel));
  if (!filePath.startsWith(ROOT)) {
    res.writeHead(403); return res.end('Forbidden');
  }
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404); return res.end('Not found');
    }
    res.writeHead(200, { 'Content-Type': contentType(filePath) });
    res.end(data);
  });
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host}`);
    if (url.pathname.startsWith('/api/')) return await handleApi(req, res, url);
    return serveStatic(req, res, url.pathname);
  } catch (e) {
    sendJson(res, 500, { error: e.message });
  }
});

if (WSS) {
  const wss = new WSS({ server, path: '/api/multiplayer' });
  wss.on('connection', (ws) => {
    ws.send(JSON.stringify({ type: 'welcome', message: 'multiplayer stub connected' }));
    ws.on('message', (raw) => {
      let msg;
      try { msg = JSON.parse(String(raw)); } catch { return; }
      if (msg.type === 'join') ws.send(JSON.stringify({ type: 'joined', room: msg.room || 'default' }));
      else if (msg.type === 'stateUpdate' || msg.type === 'chat') {
        for (const client of wss.clients) if (client.readyState === 1) client.send(JSON.stringify(msg));
      }
    });
  });
}

server.listen(PORT, () => {
  console.log(`Gaming platform running at http://localhost:${PORT}`);
  console.log(`Demo game:        http://localhost:${PORT}/index.html`);
  console.log(`Health:           http://localhost:${PORT}/api/health`);
  console.log(`Leaderboard API:  http://localhost:${PORT}/api/leaderboards/demo-game`);
  console.log(`Multiplayer WS:   ws://localhost:${PORT}/api/multiplayer${WSS ? '' : ' (install ws to enable)'}`);
});
