// Consistent API error shape for mobile clients: { error: { code, message } }

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export const badRequest = (msg, code = 'bad_request') => new ApiError(400, code, msg);
export const unauthorized = (msg = 'Authentication required') => new ApiError(401, 'unauthorized', msg);
export const forbidden = (msg = 'Not allowed') => new ApiError(403, 'forbidden', msg);
export const notFound = (msg = 'Not found') => new ApiError(404, 'not_found', msg);
export const conflict = (msg) => new ApiError(409, 'conflict', msg);

export function errorHandler(err, req, res, _next) {
  if (err instanceof ApiError) {
    return res.status(err.status).json({ error: { code: err.code, message: err.message } });
  }
  if (err?.type === 'entity.parse.failed' || err?.type === 'entity.too.large') {
    return res.status(400).json({ error: { code: 'bad_request', message: 'Invalid request body' } });
  }
  console.error(`[${req.method} ${req.path}]`, err);
  res.status(500).json({ error: { code: 'internal', message: 'Internal server error' } });
}

// Cursor-style pagination: ?limit=20&offset=0 — always returns { data, page }
export function pagination(req, defaultLimit = 20, maxLimit = 100) {
  const limit = Math.min(Math.max(parseInt(req.query.limit, 10) || defaultLimit, 1), maxLimit);
  const offset = Math.max(parseInt(req.query.offset, 10) || 0, 0);
  return { limit, offset };
}

export function paginated(data, { limit, offset }) {
  return { data, page: { limit, offset, count: data.length } };
}

// Every SELECT for a user facing the public should go through this shape.
export function publicUser(row, extra = {}) {
  if (!row) return null;
  return {
    id: row.id,
    username: row.username,
    display_name: row.display_name,
    bio: row.bio,
    avatar_url: row.avatar_url,
    created_at: row.created_at,
    ...extra,
  };
}

export function extractMentions(content) {
  const set = new Set();
  for (const m of String(content).matchAll(/@([A-Za-z0-9_]{2,30})/g)) set.add(m[1].toLowerCase());
  return [...set];
}
