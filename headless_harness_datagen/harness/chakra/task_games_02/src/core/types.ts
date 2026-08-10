// Rustwake: Core Rush — shared types for the pure rules modules.

export const BOARD_W = 12;
export const BOARD_H = 9;
export const TURN_CAP = 40;

export type Team = 'player' | 'ai';

export type TileKind =
  | 'open'
  | 'crate' // half cover: blocks movement, softens shots
  | 'container' // full cover: blocks movement + line of sight
  | 'corespawn'; // behaves as open floor

export type UnitClass = 'bruiser' | 'runner' | 'spotter';

export interface UnitStats {
  hp: number;
  move: number;
  range: number;
  dmg: number;
  ignoresHalfCover: boolean;
  label: string;
}

export const UNIT_STATS: Record<UnitClass, UnitStats> = {
  bruiser: { hp: 10, move: 3, range: 1, dmg: 4, ignoresHalfCover: false, label: 'Bruiser' },
  runner: { hp: 6, move: 5, range: 2, dmg: 2, ignoresHalfCover: false, label: 'Runner' },
  spotter: { hp: 5, move: 3, range: 5, dmg: 3, ignoresHalfCover: true, label: 'Spotter' },
};

export interface Vec {
  x: number;
  y: number;
}

export interface Unit {
  id: string;
  team: Team;
  cls: UnitClass;
  pos: Vec;
  hp: number;
  maxHp: number;
  ap: number; // action points remaining this side-turn
  acted: boolean; // true once the unit has attacked (ends its activation)
  alive: boolean;
  hasCore: boolean;
}

export interface CoreState {
  /** Tile the core lies on, or null while carried. */
  pos: Vec | null;
  carrierId: string | null;
}

export interface BoardState {
  w: number;
  h: number;
  tiles: TileKind[]; // row-major, length w*h
  /** Home extraction row (y index) per team. */
  extractionRow: Record<Team, number>;
}

export interface RngState {
  seed: number;
  /** Call count — deterministic stream position. */
  calls: number;
}

export interface GameState {
  board: BoardState;
  units: Unit[];
  core: CoreState;
  /** Side currently acting. */
  active: Team;
  /** 1-based turn counter; increments when active flips back to player. */
  turn: number;
  rng: RngState;
  mapId: string;
  difficulty: 'easy' | 'normal';
  over: boolean;
  winner: Team | 'draw' | null;
  endCause: string | null;
  matchId: string;
}

export interface MapDef {
  id: string;
  name: string;
  /** BOARD_H strings of BOARD_W chars: '.', 'c' crate, '#' container, 'X' core spawn. */
  rows: string[];
  spawns: Record<Team, { cls: UnitClass; x: number; y: number }[]>;
}

export type LogEventType =
  | 'match_start'
  | 'turn_start'
  | 'move'
  | 'attack'
  | 'hit'
  | 'miss'
  | 'unit_down'
  | 'core_pickup'
  | 'core_drop'
  | 'match_end';

export interface LogEvent {
  type: LogEventType;
  sessionId: string;
  matchId: string;
  turn: number;
  ts: number;
  data?: Record<string, unknown>;
}

export function tileAt(board: BoardState, x: number, y: number): TileKind {
  return board.tiles[y * board.w + x];
}

export function inBounds(board: BoardState, x: number, y: number): boolean {
  return x >= 0 && y >= 0 && x < board.w && y < board.h;
}

export function manhattan(a: Vec, b: Vec): number {
  return Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
}
