import { Router } from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { db, audit } from './db.js';

// Reasoning: stateless JWT (12h) authenticates both HTTP and the WebSocket
// upgrade — one credential, two transports. bcrypt cost 10: adaptive, salted,
// slow by design. OAuth2/GitHub SSO later plugs into the same sign() call.
export const JWT_SECRET = process.env.JWT_SECRET || 'dev-secret-change-me';
if (JWT_SECRET === 'dev-secret-change-me' && process.env.NODE_ENV === 'production') {
  console.warn('[security] JWT_SECRET is the development default — set it in the environment');
}

export const authRouter = Router();

function sign(id, username) {
  return jwt.sign({ sub: id, username }, JWT_SECRET, { expiresIn: '12h' });
}

authRouter.post('/register', (req, res) => {
  const { username, email, password, display_name } = req.body || {};
  if (!username || !email || !password || String(password).length < 8) {
    return res.status(400).json({ error: 'username, email and a password of 8+ chars are required' });
  }
  const exists = db.prepare('SELECT id FROM users WHERE username = ? OR email = ?').get(username, email);
  if (exists) return res.status(409).json({ error: 'username or email already taken' });
  const info = db.prepare('INSERT INTO users (username, email, password_hash, display_name) VALUES (?,?,?,?)')
    .run(username, email, bcrypt.hashSync(password, 10), display_name || username);
  audit(info.lastInsertRowid, 'user.register', 'user', info.lastInsertRowid);
  res.status(201).json({ token: sign(info.lastInsertRowid, username) });
});

authRouter.post('/login', (req, res) => {
  const { username, password } = req.body || {};
  const user = db.prepare('SELECT * FROM users WHERE username = ? OR email = ?').get(username || '', username || '');
  // Identical error for unknown user vs wrong password — no account enumeration.
  if (!user || !bcrypt.compareSync(String(password || ''), user.password_hash)) {
    return res.status(401).json({ error: 'invalid credentials' });
  }
  audit(user.id, 'user.login', 'user', user.id);
  res.json({ token: sign(user.id, user.username) });
});

authRouter.get('/me', requireAuth, (req, res) => res.json({ user: req.user }));

export function requireAuth(req, res, next) {
  const m = /^Bearer (.+)$/.exec(req.headers.authorization || '');
  if (!m) return res.status(401).json({ error: 'missing bearer token' });
  try {
    const payload = jwt.verify(m[1], JWT_SECRET);
    const user = db.prepare('SELECT id, username, email, display_name, role FROM users WHERE id = ?').get(payload.sub);
    if (!user) return res.status(401).json({ error: 'user no longer exists' });
    req.user = user;
    next();
  } catch {
    res.status(401).json({ error: 'invalid or expired token' });
  }
}

const ROLE_RANK = { member: 1, maintainer: 2, owner: 3 };
export const atLeast = (role, min) => ROLE_RANK[role] >= ROLE_RANK[min];

export function teamRole(userId, teamId) {
  const row = db.prepare('SELECT role FROM team_members WHERE team_id = ? AND user_id = ?').get(teamId, userId);
  return row ? row.role : null;
}

// Authorization lives in middleware, not route bodies — no endpoint can forget the check.
export function requireTeamRole(minRole) {
  return (req, res, next) => {
    const role = teamRole(req.user.id, Number(req.params.teamId));
    if (!role || !atLeast(role, minRole)) {
      return res.status(403).json({ error: `requires team role >= ${minRole}` });
    }
    req.teamRole = role;
    next();
  };
}
