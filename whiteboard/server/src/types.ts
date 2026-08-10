// Shared protocol types — the client's socket layer uses identical shapes.
// Keeping one source of truth for the wire format prevents drift.

export type Point = { x: number; y: number };

export type ShapeKind = 'rect' | 'circle' | 'line';
export type StrokeKind = 'freehand' | 'erase' | ShapeKind;

export interface StrokeStyle {
  color: string;
  size: number;
}

// One committed drawing operation. The room state IS an ordered list of these.
export interface Stroke {
  id: string;
  userId: string;
  kind: StrokeKind;
  style: StrokeStyle;
  // freehand/erase: polyline points. shapes: [start, end] only.
  points: Point[];
}

export interface UserInfo {
  id: string;
  name: string;
  color: string; // assigned by server so each user is visually distinct
}

export interface RoomState {
  ops: Stroke[];      // committed strokes, in draw order
  users: UserInfo[];  // currently connected
}

// Server -> client payloads
export interface RemoteSegment {
  userId: string;
  strokeId: string;
  kind: StrokeKind;
  style: StrokeStyle;
  segment: [Point, Point];
}
