// Rustwake: Core Rush — shared types for the pure rules modules.
export const BOARD_W = 12;
export const BOARD_H = 9;
export const TURN_CAP = 40;
export const UNIT_STATS = {
    bruiser: { hp: 10, move: 3, range: 1, dmg: 4, ignoresHalfCover: false, label: 'Bruiser' },
    runner: { hp: 6, move: 5, range: 2, dmg: 2, ignoresHalfCover: false, label: 'Runner' },
    spotter: { hp: 5, move: 3, range: 5, dmg: 3, ignoresHalfCover: true, label: 'Spotter' },
};
export function tileAt(board, x, y) {
    return board.tiles[y * board.w + x];
}
export function inBounds(board, x, y) {
    return x >= 0 && y >= 0 && x < board.w && y < board.h;
}
export function manhattan(a, b) {
    return Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
}
