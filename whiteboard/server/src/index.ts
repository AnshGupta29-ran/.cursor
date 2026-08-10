import express from 'express';
import http from 'node:http';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { Server } from 'socket.io';
import { RoomStore } from './rooms.ts';
import type { RemoteSegment, Stroke } from './types.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  // Default transports (polling -> websocket upgrade) — the most compatible choice.
  cors: { origin: true } // dev: Vite on :5173 proxies /socket.io anyway; open origin keeps prod single-port simple
});

const store = new RoomStore();

// Input validation lives at the socket boundary — the room logic trusts ops.
const isPoint = (p: unknown): p is { x: number; y: number } =>
  !!p && typeof (p as any).x === 'number' && typeof (p as any).y === 'number' &&
  Number.isFinite((p as any).x) && Number.isFinite((p as any).y);

function validStroke(s: any): s is Stroke {
  const kinds = ['freehand', 'erase', 'rect', 'circle', 'line'];
  return !!s && typeof s.id === 'string' && kinds.includes(s.kind) &&
    typeof s.style?.color === 'string' && typeof s.style?.size === 'number' &&
    s.style.size > 0 && s.style.size <= 100 &&
    Array.isArray(s.points) && s.points.length >= 1 && s.points.length <= 5000 &&
    s.points.every(isPoint);
}

io.on('connection', socket => {
  let roomId: string | null = null;
  let userName = 'anon';

  socket.on('room:join', (payload: { roomId?: string; name?: string }) => {
    roomId = String(payload?.roomId || 'lobby').slice(0, 64);
    userName = String(payload?.name || 'anon').slice(0, 32) || 'anon';
    const room = store.get(roomId);
    socket.join(roomId);
    const me = room.addUser(socket.id, userName);

    // Full state replay to the joiner; presence diff to everyone else.
    socket.emit('room:state', room.state());
    socket.to(roomId).emit('user:joined', me);
  });

  // Live segments: NOT stored — they exist so peers watch strokes form in real
  // time. Committed strokes (op:add) are the only thing that enters the log.
  socket.on('draw:segment', (seg: RemoteSegment) => {
    if (!roomId) return;
    socket.to(roomId).emit('draw:segment', { ...seg, userId: socket.id });
  });

  socket.on('op:add', (stroke: Stroke) => {
    if (!roomId || !validStroke(stroke)) return;
    stroke.userId = socket.id; // never trust the client to name its own user
    store.get(roomId).apply(stroke);
    socket.to(roomId).emit('op:add', stroke);
  });

  socket.on('op:undo', () => {
    if (!roomId) return;
    const removedId = store.get(roomId).undo(socket.id);
    if (removedId) io.to(roomId).emit('op:remove', { strokeId: removedId });
  });

  socket.on('op:redo', () => {
    if (!roomId) return;
    const stroke = store.get(roomId).redo(socket.id);
    if (stroke) io.to(roomId).emit('op:add', stroke);
  });

  socket.on('op:clear', () => {
    if (!roomId) return;
    store.get(roomId).clear(socket.id);
    io.to(roomId).emit('op:clear');
  });

  socket.on('disconnect', () => {
    if (!roomId) return;
    const room = store.get(roomId);
    room.removeUser(socket.id);
    socket.to(roomId).emit('user:left', { userId: socket.id });
    store.dropIfEmpty(roomId);
  });
});

app.get('/health', (req, res) => res.json({ ok: true }));

// Serve the built client in production; in dev Vite owns port 5173.
// API routes are registered BEFORE the SPA catch-all so they can't be shadowed.
const clientDist = path.join(here, '..', '..', 'client', 'dist');
if (fs.existsSync(clientDist)) {
  app.use(express.static(clientDist));
  app.use((req, res) => res.sendFile(path.join(clientDist, 'index.html')));
}

const port = Number(process.env.PORT || 3001);
server.listen(port, () => console.log(`Whiteboard server on http://localhost:${port}`));
