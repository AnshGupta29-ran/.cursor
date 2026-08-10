import { WebSocketServer } from 'ws';
import jwt from 'jsonwebtoken';
import { JWT_SECRET } from './auth.js';
import { bus } from './events.js';

// Two channel shapes: user:<id> (private notifications) and pr:<id> (shared
// presence for everyone viewing a PR). Single-node Set fanout is fine here;
// multi-node swaps this for Redis pub/sub with identical semantics.
const userSockets = new Map(); // userId -> Set<ws>
const prSubs = new Map();      // prId   -> Set<ws>

export function attachWebSocket(httpServer) {
  const wss = new WebSocketServer({ noServer: true });

  httpServer.on('upgrade', (req, socket, head) => {
    const url = new URL(req.url, 'http://localhost');
    if (url.pathname !== '/ws') return socket.destroy();
    // JWT in a query param because browsers can't set headers on WebSocket.
    // The short token lifetime (12h) bounds the exposure of it appearing in logs.
    try {
      const payload = jwt.verify(url.searchParams.get('token') || '', JWT_SECRET);
      wss.handleUpgrade(req, socket, head, ws => wss.emit('connection', ws, payload));
    } catch {
      socket.destroy();
    }
  });

  wss.on('connection', (ws, payload) => {
    const userId = payload.sub;
    if (!userSockets.has(userId)) userSockets.set(userId, new Set());
    userSockets.get(userId).add(ws);

    ws.on('message', raw => {
      try {
        const msg = JSON.parse(raw);
        if (msg.type === 'subscribe' && Number.isInteger(msg.prId)) {
          if (!prSubs.has(msg.prId)) prSubs.set(msg.prId, new Set());
          prSubs.get(msg.prId).add(ws);
        }
      } catch { /* malformed client frames are ignored, never trusted */ }
    });

    ws.on('close', () => {
      userSockets.get(userId)?.delete(ws);
      for (const set of prSubs.values()) set.delete(ws);
    });
  });
}

export function pushToUser(userId, data) {
  const msg = JSON.stringify(data);
  for (const ws of userSockets.get(userId) || []) {
    if (ws.readyState === ws.OPEN) ws.send(msg);
  }
}

// PR viewers see live refreshes when anything on that PR changes.
for (const event of ['pr.comment', 'pr.review', 'pr.status', 'pr.checklist']) {
  bus.on(event, ({ pr }) => {
    const msg = JSON.stringify({ type: 'pr.update', prId: pr.id, reason: event });
    for (const ws of prSubs.get(pr.id) || []) {
      if (ws.readyState === ws.OPEN) ws.send(msg);
    }
  });
}
