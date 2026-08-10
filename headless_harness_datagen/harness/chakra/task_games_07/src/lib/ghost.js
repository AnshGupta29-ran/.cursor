/* ─── Ghost replay engine ─── */

/**
 * Get ghost position at a given elapsed time.
 * A pure function of (keystrokeLog, elapsedMs, speedMultiplier).
 * Returns the number of characters correctly typed at that moment.
 *
 * At speed 2x, elapsedMs is scaled before looking up the log.
 * Beyond the end of the log, returns the max position (completed).
 */
export function ghostPositionAt(keystrokeLog, elapsedMs, speedMultiplier = 1) {
  if (!keystrokeLog || keystrokeLog.length === 0) return 0;

  const scaledMs = elapsedMs * speedMultiplier;

  // Find the last correct keystroke at or before scaledMs
  let lastCorrectIdx = -1;
  for (let i = 0; i < keystrokeLog.length; i++) {
    if (keystrokeLog[i].t <= scaledMs) {
      if (keystrokeLog[i].correct) {
        lastCorrectIdx = i;
      }
    } else {
      break;
    }
  }

  // Count correct chars up to last correct keystroke
  let correctCount = 0;
  for (let i = 0; i <= lastCorrectIdx; i++) {
    if (keystrokeLog[i].correct) {
      correctCount++;
    }
  }

  return correctCount;
}

/**
 * Get total correct characters in a keystroke log.
 */
export function totalCorrectChars(keystrokeLog) {
  if (!keystrokeLog) return 0;
  return keystrokeLog.filter((k) => k.correct).length;
}
