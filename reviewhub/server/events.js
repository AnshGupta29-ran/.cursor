// A tiny event bus is the spine of the modular monolith:
// routes mutate state and emit — notifications, email and the WebSocket fanout
// all subscribe. Tomorrow, notify/analytics become separate services by
// pointing this bus at Redis pub/sub instead of an in-process EventEmitter.
import { EventEmitter } from 'node:events';
export const bus = new EventEmitter();
export const emit = (type, payload) => bus.emit(type, payload);
