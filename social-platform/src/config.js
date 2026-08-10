import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');

// Minimal .env loader (no dependency). Values already in process.env win.
const envFile = path.join(ROOT, '.env');
if (fs.existsSync(envFile)) {
  for (const line of fs.readFileSync(envFile, 'utf8').split('\n')) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/i);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, '');
  }
}

const DB_PATH = path.resolve(ROOT, process.env.DB_PATH || './data/social.db');
fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });

export const config = {
  root: ROOT,
  port: Number(process.env.PORT || 3000),
  host: process.env.HOST || '0.0.0.0',
  jwtSecret: process.env.JWT_SECRET || 'dev-secret-change-me',
  tokenTtl: process.env.TOKEN_TTL || '7d',
  dbPath: DB_PATH,
  admin: {
    username: process.env.ADMIN_USERNAME || 'admin',
    password: process.env.ADMIN_PASSWORD || 'admin123',
    email: process.env.ADMIN_EMAIL || 'admin@example.com',
  },
};
