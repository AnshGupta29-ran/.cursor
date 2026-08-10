/* ─── Mulberry32 seeded PRNG ─── */
export function mulberry32(seed) {
  let s = seed | 0;
  return function () {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Deterministically pick an item from an array using seeded RNG */
export function seededPick(arr, seed) {
  const rng = mulberry32(seed);
  return arr[Math.floor(rng() * arr.length)];
}

/** Deterministically shuffle an array using seeded RNG */
export function seededShuffle(arr, seed) {
  const rng = mulberry32(seed);
  const result = [...arr];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}
