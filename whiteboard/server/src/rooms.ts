import { randomUUID } from 'node:crypto';
import type { RoomState, Stroke, UserInfo } from './types.ts';

// Room: the canonical, in-memory state for one whiteboard. Ops are the source
// of truth — a joining client renders by replaying ops in order, so everyone
// converges on identical pixels regardless of when they connected.
//
// Undo model: undo emits an op that REMOVES a stroke from the log (rather than
// popping the last one). That makes undo per-user correct — Alice undoing her
// stroke never eats Bob's newer stroke, which is what a naive stack would do.
export class Room {
  readonly id: string;
  private ops: Stroke[] = [];
  private removed: Stroke[] = []; // redo stack: last-removed restores first
  private users = new Map<string, UserInfo>();

  constructor(id: string) {
    this.id = id;
  }

  addUser(userId: string, name: string): UserInfo {
    // Color from a fixed palette, stable per join order — users are told apart
    // by color in the presence list and their live cursor segments.
    const palette = ['#e6194b', '#3cb44b', '#4363d8', '#f58231', '#911eb4', '#42d4f4', '#f032e6', '#bfef45'];
    const info: UserInfo = { id: userId, name, color: palette[this.users.size % palette.length] };
    this.users.set(userId, info);
    return info;
  }

  removeUser(userId: string): boolean {
    this.users.delete(userId);
    return this.users.size === 0; // caller deletes empty rooms to bound memory
  }

  apply(stroke: Stroke): void {
    this.ops.push(stroke);
    this.removed = []; // any new op invalidates redo history — standard undo semantics
  }

  undo(userId: string): string | null {
    // Walk backwards to the caller's most recent stroke and remove it.
    for (let i = this.ops.length - 1; i >= 0; i--) {
      if (this.ops[i].userId === userId) {
        const [op] = this.ops.splice(i, 1);
        this.removed.push(op);
        return op.id;
      }
    }
    return null;
  }

  redo(userId: string): Stroke | null {
    for (let i = this.removed.length - 1; i >= 0; i--) {
      if (this.removed[i].userId === userId) {
        const [op] = this.removed.splice(i, 1);
        this.ops.push(op); // re-append: simplest consistent rule across clients
        return op;
      }
    }
    return null;
  }

  clear(userId: string): void {
    this.ops = [];
    this.removed = [];
  }

  state(): RoomState {
    return { ops: this.ops, users: [...this.users.values()] };
  }

  get isEmpty(): boolean {
    return this.users.size === 0;
  }
}

export class RoomStore {
  private rooms = new Map<string, Room>();

  get(id: string): Room {
    let room = this.rooms.get(id);
    if (!room) {
      room = new Room(id);
      this.rooms.set(id, room);
    }
    return room;
  }

  dropIfEmpty(id: string): void {
    if (this.rooms.get(id)?.isEmpty) this.rooms.delete(id);
  }
}

export const newStrokeId = () => randomUUID();
