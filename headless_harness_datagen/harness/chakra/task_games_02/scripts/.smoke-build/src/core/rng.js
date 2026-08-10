// Seeded PRNG (mulberry32) with a serializable state: { seed, calls }.
// Reproducing a stream = re-create with seed, then fast-forward `calls` draws.
export function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
        a |= 0;
        a = (a + 0x6d2b79f5) | 0;
        let t = Math.imul(a ^ (a >>> 15), 1 | a);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}
/** A deterministic RNG whose state can be saved and restored exactly. */
export class Rng {
    seed;
    calls;
    fn;
    constructor(state) {
        this.seed = state.seed >>> 0;
        this.fn = mulberry32(this.seed);
        this.calls = 0;
        // Fast-forward to the saved stream position.
        for (let i = 0; i < state.calls; i++) {
            this.fn();
            this.calls++;
        }
    }
    /** Next float in [0, 1). */
    next() {
        this.calls++;
        return this.fn();
    }
    /** Integer in [0, n). */
    int(n) {
        return Math.floor(this.next() * n);
    }
    state() {
        return { seed: this.seed, calls: this.calls };
    }
}
