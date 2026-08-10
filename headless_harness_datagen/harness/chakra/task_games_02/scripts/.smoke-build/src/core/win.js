// Win / lose / tiebreak checks. Pure, dependency-free.
//
// Two live win paths:
//   1. Wipe the enemy crew.
//   2. Carry the core to your home extraction row.
// Turn cap 40: more units alive wins; tiebreak total HP; else draw.
import { TURN_CAP } from './types.js';
export function aliveCount(state, team) {
    return state.units.filter((u) => u.alive && u.team === team).length;
}
export function totalHp(state, team) {
    return state.units
        .filter((u) => u.alive && u.team === team)
        .reduce((s, u) => s + u.hp, 0);
}
/** Check core extraction: carrier standing on their home row. Returns winning team or null. */
export function coreExtracted(state) {
    if (!state.core.carrierId)
        return null;
    const carrier = state.units.find((u) => u.id === state.core.carrierId);
    if (!carrier || !carrier.alive)
        return null;
    const homeRow = state.board.extractionRow[carrier.team];
    return carrier.pos.y === homeRow ? carrier.team : null;
}
export function checkWin(state) {
    const extracted = coreExtracted(state);
    if (extracted) {
        return {
            over: true,
            winner: extracted,
            cause: extracted === 'player' ? 'Copperjacks extracted the core' : 'Ferroscouts extracted the core',
        };
    }
    const pAlive = aliveCount(state, 'player');
    const aAlive = aliveCount(state, 'ai');
    if (aAlive === 0 && pAlive === 0) {
        return { over: true, winner: 'draw', cause: 'Mutual wipeout' };
    }
    if (aAlive === 0) {
        return { over: true, winner: 'player', cause: 'Ferroscouts wiped out' };
    }
    if (pAlive === 0) {
        return { over: true, winner: 'ai', cause: 'Copperjacks wiped out' };
    }
    if (state.turn >= TURN_CAP) {
        if (pAlive !== aAlive) {
            const winner = pAlive > aAlive ? 'player' : 'ai';
            return { over: true, winner, cause: `Turn cap ${TURN_CAP}: more units standing` };
        }
        const pHp = totalHp(state, 'player');
        const aHp = totalHp(state, 'ai');
        if (pHp !== aHp) {
            const winner = pHp > aHp ? 'player' : 'ai';
            return { over: true, winner, cause: `Turn cap ${TURN_CAP}: higher total HP` };
        }
        return { over: true, winner: 'draw', cause: `Turn cap ${TURN_CAP}: dead even` };
    }
    return { over: false, winner: null, cause: null };
}
