import { useState } from 'react'

const COLORS = ['#00ff88', '#ff8800', '#4488ff', '#ff44aa']
const NAMES = ['JAX', 'RIOT', 'KESTREL', 'MORSE']

function generatePlayer(seedIdx) {
  return {
    id: `p_${Date.now()}_${seedIdx}`,
    name: NAMES[seedIdx % NAMES.length],
    color: COLORS[seedIdx % COLORS.length],
  }
}

function makeInitial(count) {
  return Array.from({ length: count }, (_, i) => generatePlayer(i))
}

export default function Setup({ profiles, onProfilesChange, onStart, settings }) {
  const [players, setPlayers] = useState(() => {
    if (profiles.length >= 2 && profiles.length <= 4) {
      // preserve existing
      return profiles.map((p, i) => ({
        ...p,
        color: COLORS[i % COLORS.length],
      }))
    }
    return makeInitial(3)
  })
  const [lengthClass, setLengthClass] = useState(settings.lengthClass || 'standard')

  const updatePlayer = (idx, name) => {
    const copy = [...players]
    copy[idx] = { ...copy[idx], name }
    setPlayers(copy)
  }

  const removePlayer = (idx) => {
    if (players.length <= 2) return
    const copy = players.filter((_, i) => i !== idx)
    // reassign colors
    const recolored = copy.map((p, i) => ({ ...p, color: COLORS[i % COLORS.length] }))
    setPlayers(recolored)
  }

  const addPlayer = () => {
    if (players.length >= 4) return
    const copy = [...players, generatePlayer(players.length)]
    const recolored = copy.map((p, i) => ({ ...p, color: COLORS[i % COLORS.length] }))
    setPlayers(recolored)
  }

  // Check for duplicate non-empty names
  const names = players.map((p) => p.name.trim().toLowerCase())
  const hasDuplicates = names.some((n, i) => n !== '' && names.indexOf(n) !== i)
  const hasEmpty = players.some((p) => p.name.trim() === '')
  const canStart = players.length >= 2 && !hasDuplicates && !hasEmpty

  const handleStart = () => {
    if (!canStart) return
    const trimmed = players.map((p) => ({ ...p, name: p.name.trim() }))
    onProfilesChange(trimmed)
    onStart(trimmed, lengthClass)
  }

  return (
    <div className="setup">
      <div className="panel-title">Operator Roster</div>

      {players.map((p, i) => (
        <div className="roster-row" key={p.id}>
          <div className="roster-color" style={{ background: p.color }} />
          <input
            className="input"
            placeholder={`Operator ${i + 1}`}
            value={p.name}
            onChange={(e) => updatePlayer(i, e.target.value)}
            maxLength={12}
          />
          {players.length > 2 && (
            <button className="btn danger" onClick={() => removePlayer(i)} style={{ padding: '4px 10px', fontSize: 11 }}>
              X
            </button>
          )}
        </div>
      ))}

      <div className="roster-actions">
        {players.length < 4 && (
          <button className="btn" onClick={addPlayer}>Add Operator</button>
        )}
      </div>

      {hasDuplicates && (
        <div style={{ color: 'var(--red)', fontSize: 11 }}>Duplicate call signs not allowed</div>
      )}
      {hasEmpty && (
        <div style={{ color: 'var(--red)', fontSize: 11 }}>All operators need a call sign</div>
      )}

      <div className="setup-options">
        <label>
          Length Class
          <select value={lengthClass} onChange={(e) => setLengthClass(e.target.value)}>
            <option value="short">Short</option>
            <option value="standard">Standard</option>
            <option value="burst">Burst</option>
            <option value="all">All Classes</option>
          </select>
        </label>
      </div>

      <div style={{ marginTop: 'auto', display: 'flex', gap: 8 }}>
        <button className="btn primary" disabled={!canStart} onClick={handleStart}>
          Begin Transmission
        </button>
      </div>
    </div>
  )
}
