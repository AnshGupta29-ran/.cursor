import { run } from '../db.js';
import { pushToUser } from '../realtime.js';

// Persist a notification and push it to online devices. Never notifies the actor about their own action.
export function notify(userId, actorId, type, entityId = null) {
  if (userId === actorId) return;
  try {
    const info = run(
      'INSERT INTO notifications (user_id, actor_id, type, entity_id) VALUES (?,?,?,?)',
      userId, actorId, type, entityId
    );
    pushToUser(userId, {
      type: 'notification',
      notification: { id: Number(info.lastInsertRowid), actor_id: actorId, kind: type, entity_id: entityId, created_at: new Date().toISOString() },
    });
  } catch (e) {
    console.error('notify failed:', e.message);
  }
}
