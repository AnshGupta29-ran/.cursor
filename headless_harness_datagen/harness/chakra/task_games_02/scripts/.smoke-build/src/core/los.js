// Line-of-sight and cover math. Pure, dependency-free.
//
// LOS: supercover line from attacker tile to target tile. Any intermediate
// `container` blocks the shot entirely. A `crate` adjacent to the TARGET that
// the line crosses grants half cover (softens the shot) unless the attacker
// ignores half cover (Spotter).
import { tileAt } from './types.js';
/** Grid cells strictly between a and b on the segment a->b (supercover walk). */
export function cellsBetween(a, b) {
    const cells = [];
    let x = a.x;
    let y = a.y;
    const dx = Math.abs(b.x - a.x);
    const dy = Math.abs(b.y - a.y);
    const sx = a.x < b.x ? 1 : -1;
    const sy = a.y < b.y ? 1 : -1;
    let err = dx - dy;
    while (!(x === b.x && y === b.y)) {
        const e2 = 2 * err;
        if (e2 > -dy && e2 < dx) {
            // pure step in x or y — record intermediate cell
            if (e2 > -dy) {
                err -= dy;
                x += sx;
            }
            if (e2 < dx) {
                err += dx;
                y += sy;
            }
            if (!(x === b.x && y === b.y))
                cells.push({ x, y });
        }
        else if (e2 > -dy) {
            err -= dy;
            x += sx;
            if (!(x === b.x && y === b.y))
                cells.push({ x, y });
        }
        else {
            // e2 < dx
            err += dx;
            y += sy;
            if (!(x === b.x && y === b.y))
                cells.push({ x, y });
        }
        if (cells.length > 64)
            break; // safety
    }
    return cells;
}
/**
 * Whether the target has half cover against an attacker at `from`.
 * Rule: a crate adjacent to the target that the attack line passes through.
 */
export function los(board, from, to) {
    const between = cellsBetween(from, to);
    let halfCover = false;
    for (const c of between) {
        const t = tileAt(board, c.x, c.y);
        if (t === 'container')
            return { clear: false, halfCover: false };
    }
    // Half cover: a crate orthogonally adjacent to the TARGET whose cell is
    // crossed by the line (i.e. it lies on the between-cells, or the line's
    // final approach steps over that crate direction).
    for (const c of between) {
        if (tileAt(board, c.x, c.y) === 'crate') {
            const adjacentToTarget = Math.abs(c.x - to.x) + Math.abs(c.y - to.y) === 1;
            if (adjacentToTarget)
                halfCover = true;
        }
    }
    return { clear: true, halfCover };
}
