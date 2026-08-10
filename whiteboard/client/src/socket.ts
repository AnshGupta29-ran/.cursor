import { io, type Socket } from 'socket.io-client';
import type { RemoteSegment, RoomState, Stroke, UserInfo } from './types';

// One socket for the app lifetime. Reconnection strategy:
// socket.io auto-reconnects with backoff; on 'connect' (first OR subsequent)
// we re-join the room, and the server responds with a full state replay.
// That's what makes reconnects "graceful" — the canvas simply re-renders from
// the authoritative op log, no matter what was missed while offline.
export type ConnStatus = 'connecting' | 'online' | 'offline';

interface Handlers {
  onState: (s: RoomState) => void;
  onOpAdd: (s: Stroke) => void;
  onOpRemove: (strokeId: string) => void;
  onClear: () => void;
  onSegment: (s: RemoteSegment) => void;
  onUserJoined: (u: UserInfo) => void;
  onUserLeft: (userId: string) => void;
  onStatus: (s: ConnStatus) => void;
}

export class BoardSocket {
  private socket: Socket;
  private roomId = '';
  private name = '';
  private h: Handlers;

  constructor(handlers: Handlers) {
    this.h = handlers;
    this.socket = io({ reconnectionDelayMax: 5000 });
    this.socket.on('connect', () => {
      this.h.onStatus('online');
      if (this.roomId) this.socket.emit('room:join', { roomId: this.roomId, name: this.name });
    });
    this.socket.on('disconnect', () => this.h.onStatus('offline'));
    this.socket.io.on('reconnect_attempt', () => this.h.onStatus('connecting'));
    // Delegate through this.h at call time so setHandlers can retarget them.
    this.socket.on('room:state', (s: RoomState) => this.h.onState(s));
    this.socket.on('op:add', (s: Stroke) => this.h.onOpAdd(s));
    this.socket.on('op:remove', (p: { strokeId: string }) => this.h.onOpRemove(p.strokeId));
    this.socket.on('op:clear', () => this.h.onClear());
    this.socket.on('draw:segment', (s: RemoteSegment) => this.h.onSegment(s));
    this.socket.on('user:joined', (u: UserInfo) => this.h.onUserJoined(u));
    this.socket.on('user:left', (p: { userId: string }) => this.h.onUserLeft(p.userId));
  }

  get id(): string { return this.socket.id ?? ''; }

  // Board mounts after App creates the socket — handlers are swappable so the
  // stable socket instance can retarget its callbacks without reconnecting.
  setHandlers(h: Handlers) { this.h = h; }

  join(roomId: string, name: string) {
    this.roomId = roomId;
    this.name = name;
    if (this.socket.connected) this.socket.emit('room:join', { roomId, name });
  }

  sendSegment(seg: RemoteSegment) { this.socket.emit('draw:segment', seg); }
  addStroke(stroke: Stroke) { this.socket.emit('op:add', stroke); }
  undo() { this.socket.emit('op:undo'); }
  redo() { this.socket.emit('op:redo'); }
  clear() { this.socket.emit('op:clear'); }
}
