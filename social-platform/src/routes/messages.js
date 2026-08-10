import { Router } from 'express';
import { all, get, run } from '../db.js';
import { requireAuth, requireNotMuted } from '../auth/middleware.js';
import { badRequest, forbidden, notFound, pagination, paginated, publicUser } from '../utils/http.js';
import { pushToUser } from '../realtime.js';
import { notify } from '../utils/notify.js';
import { scanText } from '../utils/moderation.js';
import { track } from '../utils/analytics.js';

export const messagesRouter = Router();

function findConversation(a, b) {
  const [lo, hi] = a < b ? [a, b] : [b, a];
  return get('SELECT * FROM conversations WHERE user_a = ? AND user_b = ?', lo, hi);
}

function createConversation(a, b) {
  const [lo, hi] = a < b ? [a, b] : [b, a];
  const info = run('INSERT INTO conversations (user_a, user_b) VALUES (?,?)', lo, hi);
  return get('SELECT * FROM conversations WHERE id = ?', info.lastInsertRowid);
}

function otherParty(convo, meId) {
  const otherId = convo.user_a === meId ? convo.user_b : convo.user_a;
  return get('SELECT * FROM users WHERE id = ?', otherId);
}

function mustBeMember(req, convoId) {
  const convo = get('SELECT * FROM conversations WHERE id = ?', convoId);
  if (!convo) throw notFound('Conversation not found');
  if (convo.user_a !== req.user.id && convo.user_b !== req.user.id) throw forbidden('Not a participant');
  return convo;
}

// List my conversations, newest activity first, with unread counts.
messagesRouter.get('/conversations', requireAuth, (req, res) => {
  const { limit, offset } = pagination(req, 30);
  const rows = all(
    `SELECT c.*,
            (SELECT content FROM messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC, m.id DESC LIMIT 1) AS last_message,
            (SELECT created_at FROM messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC, m.id DESC LIMIT 1) AS last_message_at,
            (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id AND m.sender_id != ? AND m.read_at IS NULL) AS unread_count
     FROM conversations c
     WHERE c.user_a = ? OR c.user_b = ?
     ORDER BY COALESCE(last_message_at, c.created_at) DESC LIMIT ? OFFSET ?`,
    req.user.id, req.user.id, req.user.id, limit, offset
  );
  const data = rows.map((c) => {
    const other = otherParty(c, req.user.id);
    return {
      id: c.id,
      participant: publicUser(other),
      last_message: c.last_message,
      last_message_at: c.last_message_at,
      unread_count: c.unread_count,
    };
  });
  res.json(paginated(data, { limit, offset }));
});

// Open (or create) a conversation with a user.
messagesRouter.post('/conversations', requireAuth, (req, res, next) => {
  try {
    const otherId = Number(req.body?.user_id);
    if (!Number.isInteger(otherId)) throw badRequest('user_id is required');
    if (otherId === req.user.id) throw badRequest('Cannot message yourself');
    const other = get('SELECT * FROM users WHERE id = ? AND status != \'banned\'', otherId);
    if (!other) throw notFound('User not found');
    const convo = findConversation(req.user.id, otherId) || createConversation(req.user.id, otherId);
    res.status(201).json({ conversation: { id: convo.id, participant: publicUser(other) } });
  } catch (e) { next(e); }
});

// Message history.
messagesRouter.get('/conversations/:id/messages', requireAuth, (req, res, next) => {
  try {
    const convo = mustBeMember(req, req.params.id);
    const { limit, offset } = pagination(req, 50);
    const rows = all(
      `SELECT m.*, u.username, u.display_name, u.avatar_url
       FROM messages m JOIN users u ON u.id = m.sender_id
       WHERE m.conversation_id = ?
       ORDER BY m.created_at DESC, m.id DESC LIMIT ? OFFSET ?`,
      convo.id, limit, offset
    );
    res.json(paginated(rows.map(shapeMessage).reverse(), { limit, offset }));
  } catch (e) { next(e); }
});

// Send a message. REST is the source of truth; WS pushes to online recipients.
messagesRouter.post('/conversations/:id/messages', requireAuth, requireNotMuted, (req, res, next) => {
  try {
    const convo = mustBeMember(req, req.params.id);
    const text = String(req.body?.content || '').trim();
    if (!text) throw badRequest('content is required');
    if (text.length > 4000) throw badRequest('content too long (max 4000 chars)');
    const scan = scanText(text);
    if (!scan.ok) throw badRequest(`Message rejected by content filter (${scan.matches.join(', ')})`, 'content_flagged');

    const info = run('INSERT INTO messages (conversation_id, sender_id, content) VALUES (?,?,?)', convo.id, req.user.id, text);
    const row = get(
      `SELECT m.*, u.username, u.display_name, u.avatar_url FROM messages m JOIN users u ON u.id = m.sender_id WHERE m.id = ?`,
      info.lastInsertRowid
    );
    const message = shapeMessage(row);
    track('message_send', { userId: req.user.id, entityType: 'conversation', entityId: convo.id });

    const other = otherParty(convo, req.user.id);
    pushToUser(other.id, { type: 'message', conversation_id: convo.id, message });
    pushToUser(req.user.id, { type: 'message', conversation_id: convo.id, message }); // other devices of sender
    notify(other.id, req.user.id, 'message', convo.id);

    res.status(201).json({ message });
  } catch (e) { next(e); }
});

// Mark everything in a conversation as read (read receipts).
messagesRouter.post('/conversations/:id/read', requireAuth, (req, res, next) => {
  try {
    const convo = mustBeMember(req, req.params.id);
    run(
      'UPDATE messages SET read_at = strftime(\'%Y-%m-%dT%H:%M:%fZ\',\'now\') WHERE conversation_id = ? AND sender_id != ? AND read_at IS NULL',
      convo.id, req.user.id
    );
    const other = otherParty(convo, req.user.id);
    pushToUser(other.id, { type: 'read_receipt', conversation_id: convo.id, reader_id: req.user.id });
    res.json({ ok: true });
  } catch (e) { next(e); }
});

function shapeMessage(r) {
  return {
    id: r.id,
    conversation_id: r.conversation_id,
    content: r.content,
    read_at: r.read_at,
    created_at: r.created_at,
    sender: { id: r.sender_id, username: r.username, display_name: r.display_name, avatar_url: r.avatar_url },
  };
}
