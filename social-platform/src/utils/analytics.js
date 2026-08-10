import { run } from '../db.js';

// Fire-and-forget event tracking. Never throws into request handlers.
export function track(event, { userId = null, entityType = null, entityId = null } = {}) {
  try {
    run(
      'INSERT INTO analytics_events (event, user_id, entity_type, entity_id) VALUES (?,?,?,?)',
      event, userId, entityType, entityId
    );
  } catch (e) {
    console.error('analytics track failed:', e.message);
  }
}
