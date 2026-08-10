import { useState, useEffect, useRef, useCallback } from 'react'
import { demoOperators, demoRuns } from '../data/demoData.js'
import { transmissions } from '../data/transmissions.js'
import { ghostPositionAt } from '../lib/ghost.js'
import { rankRuns, getWinner } from '../lib/race.js'
import { calcWpm, calcAccuracy } from '../lib/scoring.js'

export default function DemoDesk({ settings, onBack }) {
  const [phase, setPhase] = useState('playing') // playing | results
  const [elapsedMs, setElapsedMs] = useState(0)
  const startTimeRef = useRef(null)
  const timerRef = useRef(null)
  const [finished, setFinished] = useState(false)

  const tx = transmissions.find((t) => t.id === 't_001')
  const totalChars = tx ? tx.text.length : 1

  const ghostSpeed = settings.ghostSpeed || 1

  useEffect(() => {
    startTimeRef.current = Date.now()
    timerRef.current = setInterval(() => {
      const now = Date.now() - startTimeRef.current
      setElapsedMs(now)

      // Check if both demo runs are complete (longer riot run)
      if (now >= 9000 && !finished) {
        setFinished(true)
      }
    }, 50)

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  // When finished, wait a beat then show results
  useEffect(() => {
    if (finished) {
      const t = setTimeout(() => setPhase('results'), 1500)
      return () => clearTimeout(t)
    }
  }, [finished])

  const operatorColorMap = {}
  demoOperators.forEach((op) => { operatorColorMap[op.id] = op.color })

  // Speed control
  const [speedLabel, setSpeedLabel] = useState(ghostSpeed)

  const handleReset = useCallback(() => {
    setPhase('playing')
    setElapsedMs(0)
    setFinished(false)
    startTimeRef.current = Date.now()
    if (timerRef.current) clearInterval(timerRef.current)
    timerRef.current = setInterval(() => {
      const now = Date.now() - startTimeRef.current
      setElapsedMs(now)
      if (now >= 9000 && !finished) {
        setFinished(true)
      }
    }, 50)
  }, [])

  if (phase === 'results') {
    const ranked = rankRuns(demoRuns)
    const winnerId = getWinner(ranked)
    const winner = demoOperators.find((o) => o.id === winnerId)

    return (
      <div className="results fade-in">
        <div className="panel-title">Demo Desk — Results</div>
        {winner && (
          <div className="winner-callsign" style={{ color: winner.color }}>
            {winner.name}
          </div>
        )}
        <div style={{ color: 'var(--gray)', fontSize: 12, letterSpacing: 2 }}>
          TOP OPERATOR
        </div>

        <table className="rank-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Call Sign</th>
              <th>Time</th>
              <th>WPM</th>
              <th>Fidelity</th>
            </tr>
          </thead>
          <tbody>
            {ranked.map((r) => (
              <tr key={r.playerId} className={r.rank === 1 ? 'rank-1' : ''}>
                <td>{r.rank}</td>
                <td style={{ color: operatorColorMap[r.playerId] || '#888' }}>
                  {demoOperators.find((o) => o.id === r.playerId)?.name || '???'}
                </td>
                <td>{(r.elapsedMs / 1000).toFixed(1)}s</td>
                <td>{calcWpm(r.correctChars, r.elapsedMs).toFixed(1)}</td>
                <td>{(calcAccuracy(r.correctKeystrokes, r.totalKeystrokes) * 100).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="results-actions">
          <button className="btn" onClick={handleReset}>Replay</button>
          <button className="btn" onClick={onBack}>Back to Menu</button>
        </div>
      </div>
    )
  }

  // Playing phase — show transmission and ghost lanes
  const jaxRun = demoRuns[0]
  const riotRun = demoRuns[1]
  const jaxPos = ghostPositionAt(jaxRun.keystrokeLog, elapsedMs, ghostSpeed)
  const riotPos = ghostPositionAt(riotRun.keystrokeLog, elapsedMs, ghostSpeed)

  const jaxWpm = calcWpm(jaxPos, elapsedMs)
  const riotWpm = calcWpm(riotPos, elapsedMs)

  // Build ghost positions for display
  const ghostPositions = [
    { playerId: 'demo_jax', position: jaxPos, totalChars, name: 'JAX', color: '#00ff88' },
    { playerId: 'demo_riot', position: riotPos, totalChars, name: 'RIOT', color: '#ff8800' },
  ]

  return (
    <div className="race fade-in">
      <div className="race-hud">
        <div>
          <span style={{ color: 'var(--amber)' }}>▲ DEMO DESK</span>
        </div>
        <div>
          Time: <span>{(elapsedMs / 1000).toFixed(1)}s</span>
          &nbsp;|&nbsp; Speed: <span>{ghostSpeed}×</span>
        </div>
      </div>

      <div className="transmission-pane" style={{ opacity: 0.7 }}>
        {tx.text.split('').map((ch, i) => (
          <span key={i} className="char-pending">{ch}</span>
        ))}
      </div>

      <div className="lanes">
        {ghostPositions.map((gp) => (
          <div className="lane ghost" key={gp.playerId}>
            <div className="lane-label" style={{ color: gp.color }}>
              {gp.name}
            </div>
            <div className="lane-bar-wrap">
              <div
                className="lane-bar-fill"
                style={{
                  width: `${(gp.position / totalChars) * 100}%`,
                  background: gp.color,
                  opacity: 0.7,
                }}
              />
              <div className="lane-bar-text">
                {((gp.position / totalChars) * 100).toFixed(0)}%
              </div>
            </div>
            <div className="lane-stats">
              {(gp.playerId === 'demo_jax' ? jaxWpm : riotWpm).toFixed(0)} WPM
            </div>
          </div>
        ))}
      </div>

      <div style={{ textAlign: 'center', color: 'var(--gray)', fontSize: 11, marginTop: 8 }}>
        Watching recorded operators from actual match data.
      </div>

      <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
        <button className="btn" onClick={handleReset}>Restart Demo</button>
        <button className="btn" onClick={onBack}>Back to Menu</button>
      </div>
    </div>
  )
}
