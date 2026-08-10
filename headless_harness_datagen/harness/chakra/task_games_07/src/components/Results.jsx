import { rankRuns, getWinner } from '../lib/race.js'
import { calcWpm, calcAccuracy, calcProgress } from '../lib/scoring.js'

export default function Results({ runs, profiles, onRematch, onReseed }) {
  const ranked = rankRuns(runs)
  const winnerId = getWinner(ranked)
  const winner = profiles.find((p) => p.id === winnerId)

  const getPlayerName = (id) => profiles.find((p) => p.id === id)?.name || '???'
  const getPlayerColor = (id) => profiles.find((p) => p.id === id)?.color || '#888'

  const statusLabel = {
    finished: 'FIN',
    timeout: 'T/O',
    forfeit: 'FOR',
  }

  return (
    <div className="results fade-in">
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
            <th>Status</th>
            <th>Time</th>
            <th>WPM</th>
            <th>Fidelity</th>
            <th>Signal</th>
          </tr>
        </thead>
        <tbody>
          {ranked.map((r) => (
            <tr key={r.playerId} className={r.rank === 1 ? 'rank-1' : ''}>
              <td>{r.rank}</td>
              <td style={{ color: getPlayerColor(r.playerId) }}>
                {getPlayerName(r.playerId)}
              </td>
              <td>{statusLabel[r.status] || r.status}</td>
              <td>{(r.elapsedMs / 1000).toFixed(1)}s</td>
              <td>{calcWpm(r.correctChars, r.elapsedMs).toFixed(1)}</td>
              <td>{(calcAccuracy(r.correctKeystrokes, r.totalKeystrokes) * 100).toFixed(0)}%</td>
              <td>{(calcProgress(r.correctChars, r.totalChars) * 100).toFixed(0)}%</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="results-actions">
        <button className="btn primary" onClick={onRematch}>
          Rematch (same seed)
        </button>
        <button className="btn" onClick={onReseed}>
          New Transmission
        </button>
      </div>
    </div>
  )
}
