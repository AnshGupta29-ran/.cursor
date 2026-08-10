import http from 'node:http';
import express from 'express';
import { config } from './config.js';
import { get, run } from './db.js';
import { hashPassword } from './utils/crypto.js';
import { errorHandler } from './utils/http.js';
import { setupRealtime } from './realtime.js';
import { seedDefaultWords } from './utils/moderation.js';

import { authRouter } from './auth/routes.js';
import { usersRouter } from './routes/users.js';
import { postsRouter } from './routes/posts.js';
import { feedRouter } from './routes/feed.js';
import { notificationsRouter } from './routes/notifications.js';
import { messagesRouter } from './routes/messages.js';
import { moderationRouter } from './routes/moderation.js';
import { analyticsRouter } from './routes/analytics.js';

const API_VERSION = 'v1';

const app = express();
app.disable('x-powered-by');
app.use(express.json({ limit: '256kb' }));

// CORS for mobile/web clients. Tighten origin list for production.
app.use((req, res, next) => {
  res.set('Access-Control-Allow-Origin', '*');
  res.set('Access-Control-Allow-Headers', 'Authorization, Content-Type');
  res.set('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

// Request log (one line each, useful on mobile backends).
app.use((req, res, next) => {
  const t0 = Date.now();
  res.on('finish', () => console.log(`${req.method} ${req.originalUrl} ${res.statusCode} ${Date.now() - t0}ms`));
  next();
});

app.get('/health', (req, res) => res.json({ status: 'ok', uptime_s: Math.round(process.uptime()) }));
app.get('/api', (req, res) => res.json({ name: 'social-platform', version: API_VERSION, docs: 'see README.md' }));

app.use('/api/auth', authRouter);
app.use('/api', usersRouter);
app.use('/api', postsRouter);
app.use('/api', feedRouter);
app.use('/api', notificationsRouter);
app.use('/api', messagesRouter);
app.use('/api', moderationRouter);
app.use('/api', analyticsRouter);

app.use((req, res) => res.status(404).json({ error: { code: 'not_found', message: 'Route not found' } }));
app.use(errorHandler);

// Bootstrap an admin account and default moderation wordlist on first run.
if (!get('SELECT id FROM users WHERE role = \'admin\' LIMIT 1')) {
  run('INSERT INTO users (username, email, password_hash, display_name, role) VALUES (?,?,?,?, \'admin\')',
    config.admin.username, config.admin.email, hashPassword(config.admin.password), 'Administrator');
  console.log(`Admin account created: ${config.admin.username}`);
}
seedDefaultWords();

const server = http.createServer(app);
setupRealtime(server);

server.listen(config.port, config.host, () => {
  console.log(`social-platform API ${API_VERSION} listening on http://${config.host}:${config.port}`);
  console.log(`WebSocket endpoint: ws://<host>:${config.port}/ws?token=<jwt>`);
});
