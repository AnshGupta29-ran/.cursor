import { describe, it, expect, beforeEach } from 'vitest'
import {
  loadProfiles, saveProfiles,
  loadSettings, saveSettings,
  loadMatches, saveMatches, addMatch,
  resetAll, checkSchemaVersion,
} from './storage.js'

// Simple localStorage mock
const store = {}
beforeEach(() => {
  Object.keys(store).forEach((k) => delete store[k])
})

global.localStorage = {
  getItem: (key) => (store[key] !== undefined ? store[key] : null),
  setItem: (key, val) => { store[key] = String(val) },
  removeItem: (key) => { delete store[key] },
  clear: () => { Object.keys(store).forEach((k) => delete store[k]) },
}

describe('storage', () => {
  it('returns defaults when nothing stored', () => {
    expect(loadProfiles()).toEqual([])
    expect(loadSettings().timeCapSec).toBe(60)
  })

  it('saves and loads profiles', () => {
    const profiles = [
      { id: 'p1', name: 'JAX', color: '#00ff88' },
      { id: 'p2', name: 'RIOT', color: '#ff8800' },
    ]
    saveProfiles(profiles)
    expect(loadProfiles()).toEqual(profiles)
  })

  it('handles corrupt JSON gracefully', () => {
    store['staticline:v1:profiles'] = 'not-json{{{'
    expect(loadProfiles()).toEqual([])
  })

  it('saves and loads settings with defaults for missing keys', () => {
    saveSettings({ ghostSpeed: 2 })
    const loaded = loadSettings()
    expect(loaded.ghostSpeed).toBe(2)
    expect(loaded.timeCapSec).toBe(60) // default
  })

  it('caps matches at 10', () => {
    const match = { id: 'm1', createdAt: Date.now(), runs: [] }
    for (let i = 0; i < 15; i++) {
      addMatch({ ...match, id: `m${i}` })
    }
    const matches = loadMatches()
    expect(matches.length).toBeLessThanOrEqual(10)
  })

  it('resetAll clears everything', () => {
    saveProfiles([{ id: 'p1', name: 'JAX', color: '#00ff88' }])
    resetAll()
    expect(loadProfiles()).toEqual([])
  })
})
