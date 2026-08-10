/* ─── Scoring utilities ─── */

/**
 * Calculate WPM.
 * WPM = (correctChars / 5) / (elapsedMs / 60000)
 */
export function calcWpm(correctChars, elapsedMs) {
  if (elapsedMs <= 0) return 0;
  return (correctChars / 5) / (elapsedMs / 60000);
}

/**
 * Calculate accuracy.
 * accuracy = correctKeystrokes / totalKeystrokes
 */
export function calcAccuracy(correctKeystrokes, totalKeystrokes) {
  if (totalKeystrokes <= 0) return 1;
  return correctKeystrokes / totalKeystrokes;
}

/**
 * Calculate progress as fraction [0, 1].
 */
export function calcProgress(typedLength, totalLength) {
  if (totalLength <= 0) return 0;
  return Math.min(typedLength / totalLength, 1);
}
