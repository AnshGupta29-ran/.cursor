import { WebSocketServer } from 'ws';
import { verifyToken } from './utils/crypto.js';
import { get } from './db.js';

// In-process realtime hub. Maps userId -> Set<ws> (a user may have several devices).
const clients = new Map();

export function setupRealtime(server) {
  const wss = new WebSocketServer({ server, path: '/ws' });

  wss.on('connection', (ws, req) => {
    // Mobile clients authenticate via /ws?token=<jwt>
    const url = new URL(req.url, 'http://localhost');
    const payload = verifyToken(url.searchParams.get('token'));
    if (!payload) {
      ws.send(JSON.stringify({ type: 'error', error: 'unauthorized' }));
      return ws.close(4001, 'unauthorized');
    }
    const user = get('SELECT id, status FROM users WHERE id = ?', payload.sub);
    if (!user || user.status === 'banned') return ws.close(4003, 'forbidden');

    ws.userId = user.id;
    if (!clients.has(user.id)) clients.set(user.id, new Set());
    clients.get(user.id).add(ws);

    ws.isAlive = true;
    ws.on('pong', () => { ws.isAlive = true; });
    ws.send(JSON.stringify({ type: 'connected', user_id: user.id }));

    ws.on('message', (raw) => {
      // Client -> server WS messages (currently just ping; messages go through REST
      // so they persist even when the recipient is offline).
      try {
        const msg = JSON.parse(raw);
        if (msg.type === 'ping') ws.send(JSON.stringify({ type: 'pong', ts: Date.now() }));
      } catch { /* ignore malformed frames */ }
    });

    ws.on('close', () => {
      const set = clients.get(user.id);
      if (set) {
        set.delete(ws);
        if (set.size === 0) clients.delete(user.id);
      }
    });
  });

  const heartbeat = setInterval(() => {
    for (const set of clients.values()) {
      for (const ws of set) {
        if (!ws.isAlive) { ws.terminate(); continue; }
        ws.isAlive = false;
        ws.ping();
      }
    }
  }, 30000);
  wss.on('close', () => clearInterval(heartbeat));

  return wss;
}

// Push an event to every live connection of a user.
export function pushToUser(userId, event) {
  const set = clients.get(userId);
  if (!set) return false;
  const frame = JSON.stringify(event);
  for (const ws of set) {
    if (ws.readyState === ws.OPEN) ws.send(frame);
  }
  return true;
}

export function onlineUserIds() {
  return [...clients.keys()];
}
