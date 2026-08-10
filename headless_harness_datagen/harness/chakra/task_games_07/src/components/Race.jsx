import { useState, useEffect, useRef, useCallback } from 'react'
import { calcWpm, calcAccuracy, calcProgress } from '../lib/scoring.js'
import { ghostPositionAt } from '../lib/ghost.js'

export default function Race({
  transmission,
  activePlayer,
  ghostRuns,
  allPlayers,
  currentPlayerIdx,
  settings,
  onFinish,
}) {
  const text = transmission.text
  const totalChars = text.length

  // Keystroke log
  const logRef = useRef([])
  const startTimeRef = useRef(null)
  const [elapsedMs, setElapsedMs] = useState(0)
  const [typed, setTyped] = useState('')
  const [typedArr, setTypedArr] = useState([]) // array of { char, correct }
  const [finished, setFinished] = useState(false)
  const inputRef = useRef(null)
  const timerRef = useRef(null)
  const [pasted, setPasted] = useState(false)

  // Determine colors for ghosts
  const playerColorMap = {}
  allPlayers.forEach((p, i) => {
    playerColorMap[p.id] = p.color || ['#00ff88', '#ff8800', '#4488ff', '#ff44aa'][i % 4]
  })

  // Start timer on mount
  useEffect(() => {
    startTimeRef.current = Date.now()
    timerRef.current = setInterval(() => {
      setElapsedMs(Date.now() - startTimeRef.current)
    }, 100)

    // focus input
    if (inputRef.current) inputRef.current.focus()

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  // Check time cap
  useEffect(() => {
    if (settings.timeCapSec && elapsedMs >= settings.timeCapSec * 1000 && !finished) {
      finishRun('timeout')
    }
  }, [elapsedMs, settings.timeCapSec, finished])

  const finishRun = useCallback((status) => {
    if (finished) return
    setFinished(true)
    if (timerRef.current) clearInterval(timerRef.current)

    const finalElapsedMs = Date.now() - startTimeRef.current
    const log = logRef.current
    const correctKeystrokes = log.filter((k) => k.correct).length
    const totalKeystrokes = log.length
    const correctChars = typedArr.filter((c) => c.correct).length
    const wpm = calcWpm(correctChars, finalElapsedMs)
    const accuracy = calcAccuracy(correctKeystrokes, totalKeystrokes)
    const progress = calcProgress(correctChars, totalChars)

    onFinish({
      transmissionId: transmission.id,
      elapsedMs: finalElapsedMs,
      wpm,
      accuracy,
      progress,
      correctChars,
      totalChars,
      correctKeystrokes,
      totalKeystrokes,
      keystrokeLog: log,
      status,
    })
  }, [finished, transmission, totalChars, typedArr, onFinish])

  // Handle keystroke
  const handleKeyDown = useCallback((e) => {
    if (finished) return

    // Esc = forfeit
    if (e.key === 'Escape') {
      e.preventDefault()
      finishRun('forfeit')
      return
    }

    // Ignore modifier-only keys
    if (e.ctrlKey || e.altKey || e.metaKey) return

    // Prevent paste
    if (e.key === 'v' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      return
    }

    // Prevent typing after completion
    const currentTyped = typedArr
    const nextIdx = currentTyped.length

    if (e.key === 'Backspace') {
      e.preventDefault()
      if (nextIdx <= 0) return
      const newArr = currentTyped.slice(0, -1)
      setTypedArr(newArr)
      setTyped(newArr.map((c) => c.char).join(''))
      logRef.current.push({ t: Date.now() - startTimeRef.current, char: '\b', correct: false })
      return
    }

    // Single printable character only
    if (e.key.length !== 1) return
    e.preventDefault()

    const expected = text[nextIdx]
    const correct = e.key === expected
    const newEntry = { char: e.key, correct }
    const newArr = [...currentTyped, newEntry]
    setTypedArr(newArr)
    setTyped(newArr.map((c) => c.char).join(''))
    logRef.current.push({ t: Date.now() - startTimeRef.current, char: e.key, correct })

    // Check completion
    if (newArr.length >= totalChars) {
      finishRun('finished')
    }
  }, [finished, text, totalChars, typedArr, finishRun])

  // Prevent paste
  const handlePaste = useCallback((e) => {
    e.preventDefault()
    setPasted(true)
    setTimeout(() => setPasted(false), 1000)
  }, [])

  // Build ghost positions
  const ghostPositions = ghostRuns.map((run) => ({
    playerId: run.playerId,
    position: ghostPositionAt(run.keystrokeLog, elapsedMs, settings.ghostSpeed || 1),
    totalChars: run.totalChars || text.length,
    name: allPlayers.find((p) => p.id === run.playerId)?.name || '???',
    color: playerColorMap[run.playerId] || '#888',
  }))

  // Current player stats
  const correctCount = typedArr.filter((c) => c.correct).length
  const wpm = calcWpm(correctCount, elapsedMs)
  const accuracy = calcAccuracy(
    typedArr.filter((c) => c.correct).length,
    typedArr.length
  )
  const progress = calcProgress(correctCount, totalChars)

  const timeCapSec = settings.timeCapSec || 60
  const remainingSec = Math.max(0, timeCapSec - Math.floor(elapsedMs / 1000))

  return (
    <div className="race" onClick={() => inputRef.current?.focus()}>
      {/* HUD */}
      <div className="race-hud">
        <div>
          Operator: <span style={{ color: activePlayer?.color }}>{activePlayer?.name}</span>
        </div>
        <div>
          Key Rate: <span>{wpm.toFixed(1)}</span> WPM
          &nbsp;|&nbsp; Fidelity: <span>{(accuracy * 100).toFixed(0)}%</span>
          &nbsp;|&nbsp; Signal: <span>{(progress * 100).toFixed(0)}%</span>
          &nbsp;|&nbsp; Time: <span>{remainingSec}s</span>
        </div>
      </div>

      {/* Transmission pane with character highlighting */}
      <div className="transmission-pane">
        {text.split('').map((ch, i) => {
          const entry = typedArr[i]
          let cls = 'char-pending'
          if (entry) {
            cls = entry.correct ? 'char-correct' : 'char-incorrect'
          } else if (i === typedArr.length) {
            cls = 'char-current'
          }
          return (
            <span key={i} className={cls}>
              {ch}
            </span>
          )
        })}
      </div>

      {/* Ghost lanes */}
      <div className="lanes">
        {/* Current player lane */}
        <div className="lane active">
          <div className="lane-label" style={{ color: activePlayer?.color }}>
            {activePlayer?.name}
          </div>
          <div className="lane-bar-wrap">
            <div
              className="lane-bar-fill"
              style={{ width: `${progress * 100}%`, background: activePlayer?.color }}
            />
            <div className="lane-bar-text">
              {(progress * 100).toFixed(0)}%
            </div>
          </div>
          <div className="lane-stats">
            {wpm.toFixed(0)} WPM &middot; {(accuracy * 100).toFixed(0)}%
          </div>
        </div>

        {/* Ghost lanes */}
        {ghostPositions.map((gp) => (
          <div className="lane ghost" key={gp.playerId}>
            <div className="lane-label" style={{ color: gp.color }}>
              {gp.name} (ghost)
            </div>
            <div className="lane-bar-wrap">
              <div
                className="lane-bar-fill"
                style={{
                  width: `${(gp.position / gp.totalChars) * 100}%`,
                  background: gp.color,
                  opacity: 0.6,
                }}
              />
              <div className="lane-bar-text">
                {((gp.position / gp.totalChars) * 100).toFixed(0)}%
              </div>
            </div>
            <div className="lane-stats">
              &nbsp;
            </div>
          </div>
        ))}
      </div>

      {/* Typing area */}
      <div className="race-type-area">
        <input
          ref={inputRef}
          className="input"
          type="text"
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="off"
          spellCheck="false"
          value={typed}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          onChange={() => {}} // controlled
          placeholder={finished ? 'Run complete' : 'Type transmission here...'}
          disabled={finished}
        />
      </div>

      {pasted && (
        <div style={{ color: 'var(--red)', fontSize: 11 }}>
          Paste disabled — type the transmission manually
        </div>
      )}

      <div className="race-controls">
        <span style={{ fontSize: 10, color: 'var(--gray)' }}>
          Type to advance &middot; Backspace corrects &middot; Esc forfeits
        </span>
      </div>
    </div>
  )
}
