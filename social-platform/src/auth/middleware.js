import { get } from '../db.js';
import { verifyToken } from '../utils/crypto.js';
import { unauthorized, forbidden } from '../utils/http.js';

function loadUser(req) {
  const header = req.headers.authorization || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : null;
  const payload = token && verifyToken(token);
  if (!payload) return null;
  const user = get(
    'SELECT id, username, email, display_name, bio, avatar_url, role, status, created_at FROM users WHERE id = ?',
    payload.sub
  );
  if (!user || user.status === 'banned') return null;
  return user;
}

// Hard requirement — 401 without a valid token.
export function requireAuth(req, res, next) {
  const user = loadUser(req);
  if (!user) return next(unauthorized());
  req.user = user;
  next();
}

// Soft requirement — attaches req.user when present, continues either way.
export function optionalAuth(req, res, next) {
  req.user = loadUser(req);
  next();
}

export function requireRole(...roles) {
  return (req, res, next) => {
    if (!req.user) return next(unauthorized());
    if (!roles.includes(req.user.role)) return next(forbidden('Insufficient role'));
    next();
  };
}

// Muted users can read everything but cannot create content.
export function requireNotMuted(req, res, next) {
  if (req.user?.status === 'muted') return next(forbidden('Your account is muted'));
  next();
}
