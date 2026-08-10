import { Router } from 'express';
import { get, run } from '../db.js';
import { hashPassword, verifyPassword, signToken } from '../utils/crypto.js';
import { badRequest, unauthorized, conflict, publicUser } from '../utils/http.js';
import { requireAuth } from './middleware.js';
import { track } from '../utils/analytics.js';

export const authRouter = Router();

const USERNAME_RE = /^[A-Za-z0-9_]{3,30}$/;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function issueToken(user) {
  return signToken({ sub: user.id, username: user.username, role: user.role });
}

authRouter.post('/register', (req, res, next) => {
  try {
    const { username, email, password, display_name } = req.body || {};
    if (!USERNAME_RE.test(username || '')) throw badRequest('Username must be 3-30 chars of letters, numbers, underscores', 'invalid_username');
    if (!EMAIL_RE.test(email || '')) throw badRequest('Invalid email address', 'invalid_email');
    if (typeof password !== 'string' || password.length < 8) throw badRequest('Password must be at least 8 characters', 'weak_password');

    if (get('SELECT id FROM users WHERE username = ?', username)) throw conflict('Username already taken');
    if (get('SELECT id FROM users WHERE email = ?', email)) throw conflict('Email already registered');

    const info = run(
      'INSERT INTO users (username, email, password_hash, display_name) VALUES (?,?,?,?)',
      username, email, hashPassword(password), String(display_name || username)
    );
    const user = get('SELECT * FROM users WHERE id = ?', info.lastInsertRowid);
    track('signup', { userId: user.id, entityType: 'user', entityId: user.id });
    res.status(201).json({ token: issueToken(user), user: publicUser(user) });
  } catch (e) { next(e); }
});

authRouter.post('/login', (req, res, next) => {
  try {
    const { username, password } = req.body || {};
    if (!username || !password) throw badRequest('username and password are required');
    // Allow login with username or email.
    const user = get('SELECT * FROM users WHERE username = ? OR email = ?', username, username);
    if (!user || !verifyPassword(password, user.password_hash)) throw unauthorized('Invalid credentials');
    if (user.status === 'banned') throw unauthorized('Account is banned');
    track('login', { userId: user.id });
    res.json({ token: issueToken(user), user: publicUser(user, { email: user.email, role: user.role, status: user.status }) });
  } catch (e) { next(e); }
});

authRouter.get('/me', requireAuth, (req, res) => {
  res.json({ user: publicUser(req.user, { email: req.user.email, role: req.user.role, status: req.user.status }) });
});

authRouter.post('/change-password', requireAuth, (req, res, next) => {
  try {
    const { current_password, new_password } = req.body || {};
    if (typeof new_password !== 'string' || new_password.length < 8) throw badRequest('New password must be at least 8 characters', 'weak_password');
    const row = get('SELECT password_hash FROM users WHERE id = ?', req.user.id);
    if (!verifyPassword(current_password || '', row.password_hash)) throw unauthorized('Current password is incorrect');
    run('UPDATE users SET password_hash = ? WHERE id = ?', hashPassword(new_password), req.user.id);
    res.json({ ok: true });
  } catch (e) { next(e); }
});
