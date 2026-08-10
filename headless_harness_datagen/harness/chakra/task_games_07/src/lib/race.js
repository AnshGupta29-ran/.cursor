import { calcWpm, calcAccuracy, calcProgress } from './scoring.js';

/* ─── Race ranking / winner determination ─── */

/**
 * Rank runs for a winner screen.
 * Rules:
 *  1. finished runs sorted by elapsedMs ascending
 *  2. timeout runs sorted by progress descending, then accuracy descending
 *  3. forfeit runs sorted by progress descending, then accuracy descending
 * Overall order: finished > timeout > forfeit
 * Tie on elapsedMs: accuracy desc, then wpm desc
 *
 * Returns sorted array with a `rank` field added.
 */
export function rankRuns(runs) {
  const finished = runs
    .filter((r) => r.status === 'finished')
    .sort((a, b) => {
      if (a.elapsedMs !== b.elapsedMs) return a.elapsedMs - b.elapsedMs;
      const accDiff = calcAccuracy(b.correctKeystrokes, b.totalKeystrokes) - calcAccuracy(a.correctKeystrokes, a.totalKeystrokes);
      if (accDiff !== 0) return accDiff;
      return calcWpm(b.correctChars, b.elapsedMs) - calcWpm(a.correctChars, a.elapsedMs);
    });

  const timeout = runs
    .filter((r) => r.status === 'timeout')
    .sort((a, b) => {
      const pDiff = calcProgress(b.correctChars, b.totalChars) - calcProgress(a.correctChars, a.totalChars);
      if (pDiff !== 0) return pDiff;
      return calcAccuracy(b.correctKeystrokes, b.totalKeystrokes) - calcAccuracy(a.correctKeystrokes, a.totalKeystrokes);
    });

  const forfeit = runs
    .filter((r) => r.status === 'forfeit')
    .sort((a, b) => {
      const pDiff = calcProgress(b.correctChars, b.totalChars) - calcProgress(a.correctChars, a.totalChars);
      if (pDiff !== 0) return pDiff;
      return calcAccuracy(b.correctKeystrokes, b.totalKeystrokes) - calcAccuracy(a.correctKeystrokes, a.totalKeystrokes);
    });

  const sorted = [...finished, ...timeout, ...forfeit];
  return sorted.map((r, i) => ({ ...r, rank: i + 1 }));
}

/** Determine winner id from ranked runs, or null if no runs */
export function getWinner(rankedRuns) {
  return rankedRuns.length > 0 ? rankedRuns[0].playerId : null;
}
