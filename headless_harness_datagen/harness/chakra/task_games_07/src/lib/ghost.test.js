import { describe, it, expect } from 'vitest'
import { ghostPositionAt, totalCorrectChars } from './ghost.js'

describe('ghostPositionAt', () => {
  const log = [
    { t: 0, char: 'A', correct: true },
    { t: 500, char: 'B', correct: true },
    { t: 1000, char: 'C', correct: true },
    { t: 1500, char: 'D', correct: false },
    { t: 2000, char: '\b', correct: false },
    { t: 2500, char: 'D', correct: true },
  ]

  it('returns 0 for empty log', () => {
    expect(ghostPositionAt([], 1000)).toBe(0)
    expect(ghostPositionAt(null, 1000)).toBe(0)
  })

  it('returns correct count at the start', () => {
    expect(ghostPositionAt(log, 0)).toBe(1) // A
  })

  it('returns correct count mid-log', () => {
    expect(ghostPositionAt(log, 750)).toBe(2) // A, B
    expect(ghostPositionAt(log, 1250)).toBe(3) // A, B, (C is correct, D is not)
  })

  it('handles backspace corrections', () => {
    // At t=3000: A, B, C, D (correct back) => 4 correct
    expect(ghostPositionAt(log, 3000)).toBe(4)
  })

  it('returns max position beyond log end', () => {
    expect(ghostPositionAt(log, 999999)).toBe(4)
  })

  it('applies speed multiplier', () => {
    // At 2x, elapsed 500ms => scaled 1000ms => pos at t=1000 => 3
    expect(ghostPositionAt(log, 500, 2)).toBe(3)
    // At 0.5x, elapsed 2000ms => scaled 1000ms => pos at t=1000 => 3
    expect(ghostPositionAt(log, 2000, 0.5)).toBe(3)
  })
})

describe('totalCorrectChars', () => {
  it('counts correct chars excluding backspace', () => {
    const log = [
      { t: 0, char: 'A', correct: true },
      { t: 500, char: 'B', correct: false },
      { t: 1000, char: '\b', correct: false },
      { t: 1500, char: 'B', correct: true },
    ]
    expect(totalCorrectChars(log)).toBe(2)
  })

  it('returns 0 for null/empty', () => {
    expect(totalCorrectChars(null)).toBe(0)
    expect(totalCorrectChars([])).toBe(0)
  })
})
