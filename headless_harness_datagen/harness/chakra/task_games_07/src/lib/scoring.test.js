import { describe, it, expect } from 'vitest'
import { calcWpm, calcAccuracy, calcProgress } from './scoring.js'

describe('calcWpm', () => {
  it('returns 0 for zero elapsed time', () => {
    expect(calcWpm(50, 0)).toBe(0)
  })

  it('calculates WPM correctly', () => {
    // 50 correct chars in 60000ms => (50/5) / 1 = 10 WPM
    expect(calcWpm(50, 60000)).toBeCloseTo(10, 1)
    // 250 chars in 60000ms => 50 WPM
    expect(calcWpm(250, 60000)).toBeCloseTo(50, 1)
    // 250 chars in 30000ms => 100 WPM
    expect(calcWpm(250, 30000)).toBeCloseTo(100, 1)
  })
})

describe('calcAccuracy', () => {
  it('returns 1 for zero total', () => {
    expect(calcAccuracy(0, 0)).toBe(1)
  })

  it('calculates accuracy correctly', () => {
    expect(calcAccuracy(45, 50)).toBeCloseTo(0.9, 2)
    expect(calcAccuracy(50, 50)).toBe(1)
    expect(calcAccuracy(0, 10)).toBe(0)
  })
})

describe('calcProgress', () => {
  it('returns 0 for zero total', () => {
    expect(calcProgress(10, 0)).toBe(0)
  })

  it('calculates progress correctly', () => {
    expect(calcProgress(25, 100)).toBe(0.25)
    expect(calcProgress(100, 100)).toBe(1)
    expect(calcProgress(0, 100)).toBe(0)
  })
})
