// Scrapbrain — documented utility-scoring AI (NOT random).
//
// For each living AI unit, Scrapbrain enumerates candidate actions:
//   - attack each reachable enemy (move+shoot or shoot in place)
//   - move toward / pick up the core
//   - move toward the enemy carrier
//   - move to end next to cover
//   - retreat when HP <= 2
//   - pass
// Each candidate gets a scalar utility; the best wins. Ties are broken by the
// seeded match RNG. Easy difficulty: 15% of the time the SECOND-best action is
// taken (a "blunder").
//
// This module is pure: no DOM, no worker APIs — importable by tests, the
// worker, and the main-thread fallback alike.
import { Rng } from './rng.js';
import { UNIT_STATS, manhattan, tileAt, } from './types.js';
import { legalMoves, enemiesOf, applyMove, applyAttack, applyPickup } from './game.js';
import { previewShot } from './combat.js';
import { isAdjacent } from './board.js';
import { los } from './los.js';
function coverBonusAt(state, pos, enemies) {
    // Ending next to a crate is worth a bit when enemies could shoot us.
    let bonus = 0;
    const dirs = [
        { x: 1, y: 0 },
        { x: -1, y: 0 },
        { x: 0, y: 1 },
        { x: 0, y: -1 },
    ];
    for (const d of dirs) {
        const nx = pos.x + d.x;
        const ny = pos.y + d.y;
        if (nx < 0 || ny < 0 || nx >= state.board.w || ny >= state.board.h)
            continue;
        if (tileAt(state.board, nx, ny) === 'crate')
            bonus += 0.6;
        if (tileAt(state.board, nx, ny) === 'container')
            bonus += 0.4;
    }
    return enemies.length > 0 ? bonus : 0;
}
/** Score every candidate action for one unit. Exported for tests. */
export function scoreActions(state, unit, team) {
    const enemies = enemiesOf(state, team);
    const out = [];
    const moves = legalMoves(state, unit);
    const myHome = state.board.extractionRow[team];
    // Carrier behavior: run home.
    if (unit.hasCore) {
        for (const [key] of moves) {
            const [x, y] = key.split(',').map(Number);
            const distNow = Math.abs(unit.pos.y - myHome);
            const distNew = Math.abs(y - myHome);
            let score = 40 + (distNow - distNew) * 8;
            if (y === myHome)
                score += 1000; // extraction wins the match
            out.push({ action: { kind: 'move', unitId: unit.id, to: { x, y } }, score });
        }
        out.push({ action: { kind: 'pass', unitId: unit.id }, score: 1 });
        return out;
    }
    // Attack candidates (in place or after a move).
    for (const enemy of enemies) {
        // In place.
        const inPlace = previewShot(state, unit, enemy);
        if (unit.ap >= 1 && !unit.acted && inPlace.canShoot) {
            let score = 30 + inPlace.dmg * 6 + inPlace.chance * 20;
            if (enemy.hasCore)
                score += 50; // drop the carrier!
            if (enemy.hp <= inPlace.dmg)
                score += 25; // likely kill
            out.push({ action: { kind: 'attack', unitId: unit.id, targetId: enemy.id }, score });
        }
        // After a move.
        if (unit.ap >= 2 && !unit.acted) {
            for (const [key] of moves) {
                const [x, y] = key.split(',').map(Number);
                const dist = manhattan({ x, y }, enemy.pos);
                if (dist > UNIT_STATS[unit.cls].range)
                    continue;
                const r = los(state.board, { x, y }, enemy.pos);
                if (!r.clear)
                    continue;
                const coverApplies = r.halfCover && !UNIT_STATS[unit.cls].ignoresHalfCover;
                const chance = coverApplies ? 0.55 : 0.8;
                let score = 24 + UNIT_STATS[unit.cls].dmg * 6 + chance * 18;
                if (enemy.hasCore)
                    score += 45;
                if (enemy.hp <= UNIT_STATS[unit.cls].dmg)
                    score += 22;
                score += coverBonusAt(state, { x, y }, enemies) * 0.5;
                out.push({
                    action: { kind: 'attack', unitId: unit.id, targetId: enemy.id, moveTo: { x, y } },
                    score,
                });
            }
        }
    }
    // Core objectives.
    const corePos = state.core.pos;
    const enemyCarrier = state.core.carrierId
        ? enemies.find((e) => e.id === state.core.carrierId)
        : undefined;
    for (const [key] of moves) {
        const [x, y] = key.split(',').map(Number);
        const dest = { x, y };
        let score = 2; // base: repositioning is mildly useful
        if (corePos) {
            const dNow = manhattan(unit.pos, corePos);
            const dNew = manhattan(dest, corePos);
            score += (dNow - dNew) * 6;
            if (isAdjacent(dest, corePos) || (dest.x === corePos.x && dest.y === corePos.y)) {
                // Can pick up (needs 1 AP left after the move).
                if (unit.ap >= 2 && !unit.acted)
                    score += 35;
                else
                    score += 8;
            }
        }
        if (enemyCarrier) {
            const dNow = manhattan(unit.pos, enemyCarrier.pos);
            const dNew = manhattan(dest, enemyCarrier.pos);
            score += (dNow - dNew) * 7;
        }
        // Retreat when badly hurt.
        if (unit.hp <= 2) {
            const nearest = Math.min(...enemies.map((e) => manhattan(dest, e.pos)), 99);
            score += nearest * 5;
        }
        score += coverBonusAt(state, dest, enemies);
        out.push({ action: { kind: 'move', unitId: unit.id, to: dest }, score });
    }
    // Pickup in place.
    if (corePos && unit.ap >= 1 && !unit.acted) {
        if (isAdjacent(unit.pos, corePos) || (unit.pos.x === corePos.x && unit.pos.y === corePos.y)) {
            out.push({ action: { kind: 'pickup', unitId: unit.id }, score: 45 });
        }
    }
    out.push({ action: { kind: 'pass', unitId: unit.id }, score: unit.hp <= 2 ? 3 : 1 });
    return out;
}
/** Choose one action for the unit (best, or second-best on an Easy blunder). */
export function chooseAction(state, unit, team, rng, difficulty) {
    const scored = scoreActions(state, unit, team);
    // Stable sort descending by score; seeded tie-break by tiny random jitter.
    for (const s of scored)
        s.score += rng.next() * 0.001;
    scored.sort((a, b) => b.score - a.score);
    if (difficulty === 'easy' && scored.length > 1 && rng.next() < 0.15) {
        return scored[1].action;
    }
    return scored[0].action;
}
function perform(state, rng, action, log) {
    const unit = state.units.find((u) => u.id === action.unitId);
    if (!unit || !unit.alive)
        return;
    switch (action.kind) {
        case 'attack': {
            const target = state.units.find((u) => u.id === action.targetId);
            if (!target)
                return;
            if (action.moveTo)
                applyMove(state, unit, action.moveTo, log);
            applyAttack(state, rng, unit, target, log);
            break;
        }
        case 'move':
            applyMove(state, unit, action.to, log);
            break;
        case 'pickup':
            applyPickup(state, unit, log);
            break;
        case 'pass':
            unit.ap = 0;
            unit.acted = true;
            break;
    }
}
/**
 * Run the full AI side-turn: each living unit acts (up to its AP), chosen by
 * utility scoring. Mutates state; emits logs through `log`.
 */
export function runAiTurn(state, team, rng, log) {
    if (state.over)
        return;
    const units = state.units.filter((u) => u.alive && u.team === team);
    for (const unit of units) {
        let guard = 8;
        while (!state.over && unit.alive && unit.ap > 0 && !unit.acted && guard-- > 0) {
            const before = `${unit.pos.x},${unit.pos.y},${unit.ap}`;
            const action = chooseAction(state, unit, team, rng, state.difficulty);
            perform(state, rng, action, log);
            // Safety: if nothing changed, force pass to avoid infinite loops.
            const after = `${unit.pos.x},${unit.pos.y},${unit.ap}`;
            if (before === after) {
                unit.ap = 0;
                unit.acted = true;
            }
        }
    }
}
/** One AI decision for a single unit — the worker entry point. */
export function decideForUnit(state, unitId, rngState) {
    const rng = new Rng(rngState);
    const unit = state.units.find((u) => u.id === unitId);
    if (!unit || !unit.alive)
        return { action: { kind: 'pass', unitId }, rngState: rng.state() };
    const action = chooseAction(state, unit, unit.team, rng, state.difficulty);
    return { action, rngState: rng.state() };
}
