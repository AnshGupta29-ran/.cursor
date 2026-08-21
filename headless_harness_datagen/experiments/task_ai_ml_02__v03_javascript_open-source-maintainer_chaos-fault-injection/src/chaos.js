// chaos.js – simple fault‑injection utilities

/**
 * If the environment variable CHAOS_INJECT is set to "1", there is a
 * 20 % chance that the provided CSV line will be corrupted by flipping a
 * random character. This mimics flaky disk writes or merge conflicts.
 */
export function maybeInject(line) {
  if (process.env.CHAOS_INJECT !== '1') return line;
  // 20% probability
  if (Math.random() < 0.2) {
    // flip a random character in the string
    const idx = Math.floor(Math.random() * line.length);
    const charCode = line.charCodeAt(idx);
    // Change to a nearby printable ASCII code
    const newChar = String.fromCharCode(((charCode - 32 + 1) % 95) + 32);
    return line.substring(0, idx) + newChar + line.substring(idx + 1);
  }
  return line;
}
