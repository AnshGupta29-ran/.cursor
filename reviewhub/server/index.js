import express from 'express';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { authRouter } from './auth.js';
import { api } from './routes.js';
import { analyticsRouter } from './analytics.js';
import { attachWebSocket, pushToUser } from './ws.js';
import { registerWebSocket } from './notify.js';

const here = path.dirname(fileURLToPath(import.meta.url));

// createApp() is separated from listen() so tests can spin up a server on an
// ephemeral port without touching process state or the real database file.
export function createApp() {
  const app = express();
  app.use(express.json({ limit: '1mb' })); // 1mb cap: diffs are text; anything bigger is abuse
  app.use((req, res, next) => { console.log(`${req.method} ${req.url}`); next(); });

  // Health before the auth wall — load balancers must reach it without a token.
  app.get('/api/health', (req, res) => res.json({ ok: true }));

  app.use('/api/auth', authRouter);
  app.use('/api', api);
  app.use('/api', analyticsRouter);

  // Static SPA last, so /api never collides with frontend routes. The catch-all
  // uses a middleware (not app.get('*')) so it works on both Express 4 and 5.
  app.use(express.static(path.join(here, '..', 'public')));
  app.use((req, res) => res.sendFile(path.join(here, '..', 'public', 'index.html')));

  // One error shape everywhere — the frontend renders `error` verbatim.
  app.use((err, req, res, next) => {
    console.error(err);
    res.status(500).json({ error: 'internal server error' });
  });
  return app;
}

if (process.argv[1] && process.argv[1].endsWith('index.js')) {
  const app = createApp();
  const server = http.createServer(app);
  attachWebSocket(server);
  registerWebSocket(pushToUser);
  const port = Number(process.env.PORT || 3000);
  server.listen(port, () => console.log(`ReviewHub listening on http://localhost:${port}`));
}
