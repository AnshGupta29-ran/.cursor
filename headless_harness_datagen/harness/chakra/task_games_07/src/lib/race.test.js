import { describe, it, expect } from 'vitest'
import { rankRuns, getWinner } from './race.js'

describe('rankRuns', () => {
  const baseRun = {
    transmissionId: 't_001',
    correctChars: 40,
    totalChars: 50,
    correctKeystrokes: 45,
    totalKeystrokes: 50,
    keystrokeLog: [],
  }

  it('ranks finished runs by elapsed time ascending', () => {
    const runs = [
      { ...baseRun, playerId: 'p1', elapsedMs: 30000, status: 'finished' },
      { ...baseRun, playerId: 'p2', elapsedMs: 20000, status: 'finished' },
    ]
    const ranked = rankRuns(runs)
    expect(ranked[0].playerId).toBe('p2')
    expect(ranked[1].playerId).toBe('p1')
  })

  it('puts finished above timeout above forfeit', () => {
    const runs = [
      { ...baseRun, playerId: 'p1', elapsedMs: 30000, status: 'finished' },
      { ...baseRun, playerId: 'p2', elapsedMs: 0, status: 'forfeit', correctChars: 10 },
      { ...baseRun, playerId: 'p3', elapsedMs: 61000, status: 'timeout', correctChars: 20 },
    ]
    const ranked = rankRuns(runs)
    expect(ranked[0].playerId).toBe('p1')
    expect(ranked[1].playerId).toBe('p3')
    expect(ranked[2].playerId).toBe('p2')
  })

  it('breaks elapsed time tie by accuracy then WPM', () => {
    const runs = [
      {
        ...baseRun, playerId: 'p1', elapsedMs: 30000, status: 'finished',
        correctKeystrokes: 45, totalKeystrokes: 50, correctChars: 40,
      },
      {
        ...baseRun, playerId: 'p2', elapsedMs: 30000, status: 'finished',
        correctKeystrokes: 48, totalKeystrokes: 50, correctChars: 40,
      },
    ]
    const ranked = rankRuns(runs)
    // p2 has higher accuracy
    expect(ranked[0].playerId).toBe('p2')
  })

  it('handles empty runs array', () => {
    expect(rankRuns([])).toEqual([])
  })

  it('assigns sequential ranks', () => {
    const runs = [
      { ...baseRun, playerId: 'p1', elapsedMs: 30000, status: 'finished' },
      { ...baseRun, playerId: 'p2', elapsedMs: 35000, status: 'finished' },
      { ...baseRun, playerId: 'p3', elapsedMs: 40000, status: 'finished' },
    ]
    const ranked = rankRuns(runs)
    expect(ranked.map((r) => r.rank)).toEqual([1, 2, 3])
  })
})

describe('getWinner', () => {
  it('returns the first ranked run player id', () => {
    const runs = [
      { playerId: 'p1', elapsedMs: 20000, status: 'finished', correctChars: 40, totalChars: 50, correctKeystrokes: 45, totalKeystrokes: 50, transmissionId: 't_001', keystrokeLog: [] },
      { playerId: 'p2', elapsedMs: 30000, status: 'finished', correctChars: 40, totalChars: 50, correctKeystrokes: 45, totalKeystrokes: 50, transmissionId: 't_001', keystrokeLog: [] },
    ]
    expect(getWinner(rankRuns(runs))).toBe('p1')
  })

  it('returns null for empty runs', () => {
    expect(getWinner([])).toBe(null)
  })
})
