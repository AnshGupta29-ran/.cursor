// Client-side wire types — kept structurally identical to server/src/types.ts.
export type Point = { x: number; y: number };
export type ShapeKind = 'rect' | 'circle' | 'line';
export type StrokeKind = 'freehand' | 'erase' | ShapeKind;
export type Tool = 'pen' | 'eraser' | ShapeKind;

export interface StrokeStyle { color: string; size: number }

export interface Stroke {
  id: string;
  userId: string;
  kind: StrokeKind;
  style: StrokeStyle;
  points: Point[];
}

export interface UserInfo { id: string; name: string; color: string }
export interface RoomState { ops: Stroke[]; users: UserInfo[] }

export interface RemoteSegment {
  userId: string;
  strokeId: string;
  kind: StrokeKind;
  style: StrokeStyle;
  segment: [Point, Point];
}
