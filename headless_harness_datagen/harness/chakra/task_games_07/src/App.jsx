import { useState, useEffect, useCallback } from 'react'
import Menu from './components/Menu.jsx'
import Setup from './components/Setup.jsx'
import Race from './components/Race.jsx'
import Results from './components/Results.jsx'
import History from './components/History.jsx'
import SettingsView from './components/SettingsView.jsx'
import DemoDesk from './components/DemoDesk.jsx'
import Countdown from './components/Countdown.jsx'
import { checkSchemaVersion, initSchema, loadProfiles, saveProfiles, loadMatches, loadSettings, saveSettings, addMatch } from './lib/storage.js'
import { transmissions } from './data/transmissions.js'
import { mulberry32, seededPick } from './lib/rng.js'

const VIEWS = ['menu', 'setup', 'countdown', 'race', 'results', 'history', 'settings', 'demo']

export default function App() {
  const [view, setView] = useState('menu')
  const [settings, setSettings] = useState(() => loadSettings())
  const [profiles, setProfiles] = useState(() => loadProfiles())
  const [matches, setMatches] = useState(() => loadMatches())

  // Match state
  const [matchId, setMatchId] = useState(null)
  const [seed, setSeed] = useState(null)
  const [transmission, setTransmission] = useState(null)
  const [runs, setRuns] = useState([])  // completed runs so far
  const [currentPlayerIdx, setCurrentPlayerIdx] = useState(0)

  useEffect(() => {
    checkSchemaVersion()
    initSchema()
  }, [])

  // Persist settings
  useEffect(() => { saveSettings(settings) }, [settings])
  useEffect(() => { saveProfiles(profiles) }, [profiles])

  const resetMatch = useCallback(() => {
    setMatchId(null)
    setSeed(null)
    setTransmission(null)
    setRuns([])
    setCurrentPlayerIdx(0)
  }, [])

  const goTo = useCallback((v) => setView(v), [])

  const startNewMatch = useCallback((playerProfiles, lengthClass) => {
    const newSeed = Date.now()
    const rng = mulberry32(newSeed)
    const filtered = lengthClass === 'all'
      ? transmissions
      : transmissions.filter((t) => t.lengthClass === lengthClass)
    const tx = filtered.length > 0
      ? seededPick(filtered, newSeed)
      : seededPick(transmissions, newSeed)
    const newMatchId = `match_${newSeed}`
    setMatchId(newMatchId)
    setSeed(newSeed)
    setTransmission(tx)
    setProfiles(playerProfiles)
    setRuns([])
    setCurrentPlayerIdx(0)
    goTo('countdown')
  }, [goTo])

  const finishRun = useCallback((runData) => {
    const newRuns = [...runs, { playerId: profiles[currentPlayerIdx].id, ...runData }]
    setRuns(newRuns)
    if (currentPlayerIdx + 1 < profiles.length) {
      setCurrentPlayerIdx((i) => i + 1)
    } else {
      // All runs done — save match and go to results
      const match = {
        id: matchId,
        seed,
        transmissionId: transmission.id,
        runs: newRuns,
        createdAt: Date.now(),
      }
      addMatch(match)
      setMatches(loadMatches())
      goTo('results')
    }
  }, [runs, matchId, seed, transmission, profiles, currentPlayerIdx, goTo])

  const handleRematch = useCallback(() => {
    // Same seed => same transmission
    setCurrentPlayerIdx(0)
    setRuns([])
    goTo('countdown')
  }, [goTo])

  const handleReseed = useCallback(() => {
    const newSeed = Date.now()
    const tx = seededPick(transmissions, newSeed)
    const newMatchId = `match_${newSeed}`
    setMatchId(newMatchId)
    setSeed(newSeed)
    setTransmission(tx)
    setCurrentPlayerIdx(0)
    setRuns([])
    goTo('countdown')
  }, [goTo])

  const updateSettings = useCallback((patch) => {
    setSettings((s) => ({ ...s, ...patch }))
  }, [])

  const clearHistory = useCallback(() => {
    setMatches([])
    localStorage.removeItem('staticline:v1:matches')
  }, [])

  const activePlayer = profiles.length > 0 && currentPlayerIdx < profiles.length
    ? profiles[currentPlayerIdx]
    : null
  const ghostRuns = runs  // all prior runs become ghosts

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Staticline</h1>
          <div className="sub">Intercept Desk</div>
        </div>
        {view !== 'menu' && (
          <button className="btn" onClick={() => { resetMatch(); goTo('menu') }}>
            Menu
          </button>
        )}
      </header>

      <div className="view fade-in" key={view}>
        {view === 'menu' && (
          <Menu onSelect={(v) => goTo(v)} />
        )}
        {view === 'setup' && (
          <Setup
            profiles={profiles}
            onProfilesChange={setProfiles}
            onStart={startNewMatch}
            settings={settings}
          />
        )}
        {view === 'countdown' && (
          <Countdown
            onDone={() => goTo('race')}
          />
        )}
        {view === 'race' && (
          <Race
            key={`race_${currentPlayerIdx}_${matchId}`}
            transmission={transmission}
            activePlayer={activePlayer}
            ghostRuns={ghostRuns}
            allPlayers={profiles}
            currentPlayerIdx={currentPlayerIdx}
            settings={settings}
            onFinish={finishRun}
          />
        )}
        {view === 'results' && (
          <Results
            runs={runs}
            profiles={profiles}
            onRematch={handleRematch}
            onReseed={handleReseed}
          />
        )}
        {view === 'history' && (
          <History
            matches={matches}
            profiles={profiles}
            onClear={clearHistory}
          />
        )}
        {view === 'settings' && (
          <SettingsView
            settings={settings}
            onUpdate={updateSettings}
          />
        )}
        {view === 'demo' && (
          <DemoDesk
            settings={settings}
            onBack={() => goTo('menu')}
          />
        )}
      </div>
    </div>
  )
}
