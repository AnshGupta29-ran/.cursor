import { describe, it, expect } from 'vitest'
import { mulberry32, seededPick, seededShuffle } from './rng.js'

describe('mulberry32', () => {
  it('produces deterministic results from same seed', () => {
    const rng1 = mulberry32(42)
    const rng2 = mulberry32(42)
    for (let i = 0; i < 20; i++) {
      expect(rng1()).toBe(rng2())
    }
  })

  it('produces different results from different seeds', () => {
    const rng1 = mulberry32(42)
    const rng2 = mulberry32(99)
    const vals1 = Array.from({ length: 5 }, () => rng1())
    const vals2 = Array.from({ length: 5 }, () => rng2())
    expect(vals1).not.toEqual(vals2)
  })

  it('returns values between 0 and 1', () => {
    const rng = mulberry32(12345)
    for (let i = 0; i < 100; i++) {
      const v = rng()
      expect(v).toBeGreaterThanOrEqual(0)
      expect(v).toBeLessThan(1)
    }
  })
})

describe('seededPick', () => {
  it('returns the same item for same seed', () => {
    const arr = ['alpha', 'bravo', 'charlie', 'delta']
    const pick1 = seededPick(arr, 42)
    const pick2 = seededPick(arr, 42)
    expect(pick1).toBe(pick2)
  })

  it('returns an item from the array', () => {
    const arr = ['alpha', 'bravo']
    const pick = seededPick(arr, 77)
    expect(arr).toContain(pick)
  })
})

describe('seededShuffle', () => {
  it('returns all original elements', () => {
    const arr = [1, 2, 3, 4, 5]
    const shuffled = seededShuffle(arr, 42)
    expect(shuffled.sort()).toEqual(arr.sort())
  })

  it('is deterministic', () => {
    const arr = [1, 2, 3, 4, 5]
    const s1 = seededShuffle(arr, 42)
    const s2 = seededShuffle(arr, 42)
    expect(s1).toEqual(s2)
  })

  it('does not mutate the original array', () => {
    const arr = [1, 2, 3]
    const copy = [...arr]
    seededShuffle(arr, 42)
    expect(arr).toEqual(copy)
  })
})
