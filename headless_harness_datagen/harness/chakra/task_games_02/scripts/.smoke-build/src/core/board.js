// Movement rules: BFS around obstacles. Pure, dependency-free.
import { inBounds, tileAt } from './types.js';
/** Tiles a unit may not enter (movement-blocking). */
export function blocksMovement(board, x, y) {
    const t = tileAt(board, x, y);
    return t === 'crate' || t === 'container';
}
export function unitAt(state, x, y) {
    for (const u of state.units) {
        if (u.alive && u.pos.x === x && u.pos.y === y)
            return u;
    }
    return null;
}
const DIRS = [
    { x: 1, y: 0 },
    { x: -1, y: 0 },
    { x: 0, y: 1 },
    { x: 0, y: -1 },
];
/**
 * BFS movement range from `from` with the given move budget.
 * Occupied tiles block pathing but the unit's own tile is free.
 * Returns a map key "x,y" -> steps used.
 */
export function movementRange(state, from, budget, ignoreUnitId) {
    const board = state.board;
    const reached = new Map();
    const key = (x, y) => `${x},${y}`;
    const queue = [{ x: from.x, y: from.y, d: 0 }];
    reached.set(key(from.x, from.y), 0);
    while (queue.length > 0) {
        const cur = queue.shift();
        if (cur.d >= budget)
            continue;
        for (const dir of DIRS) {
            const nx = cur.x + dir.x;
            const ny = cur.y + dir.y;
            if (!inBounds(board, nx, ny))
                continue;
            if (blocksMovement(board, nx, ny))
                continue;
            const occ = unitAt(state, nx, ny);
            if (occ && occ.id !== ignoreUnitId)
                continue;
            const k = key(nx, ny);
            if (reached.has(k))
                continue;
            reached.set(k, cur.d + 1);
            queue.push({ x: nx, y: ny, d: cur.d + 1 });
        }
    }
    return reached;
}
/** Chebyshev-free 4-neighborhood adjacency check. */
export function isAdjacent(a, b) {
    return Math.abs(a.x - b.x) + Math.abs(a.y - b.y) === 1;
}
/** Nearest open, unoccupied tile adjacent to `pos` (for core drops). */
export function nearestOpenAdjacent(state, pos) {
    const board = state.board;
    let best = null;
    let bestDist = Infinity;
    // Search ring by ring (BFS) for an open, unoccupied tile adjacent to pos.
    for (const dir of DIRS) {
        const nx = pos.x + dir.x;
        const ny = pos.y + dir.y;
        if (!inBounds(board, nx, ny))
            continue;
        if (blocksMovement(board, nx, ny))
            continue;
        if (unitAt(state, nx, ny))
            continue;
        const d = Math.abs(nx - pos.x) + Math.abs(ny - pos.y);
        if (d < bestDist) {
            bestDist = d;
            best = { x: nx, y: ny };
        }
    }
    if (best)
        return best;
    // Fallback: any open unoccupied tile on the board (pathological boxes).
    for (let y = 0; y < board.h; y++) {
        for (let x = 0; x < board.w; x++) {
            if (!blocksMovement(board, x, y) && !unitAt(state, x, y))
                return { x, y };
        }
    }
    return null;
}
