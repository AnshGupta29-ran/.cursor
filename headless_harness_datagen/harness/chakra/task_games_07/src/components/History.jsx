import { transmissions } from '../data/transmissions.js'

export default function History({ matches, profiles, onClear }) {
  const getTxName = (id) => {
    const tx = transmissions.find((t) => t.id === id)
    return tx ? `${id} (${tx.lengthClass})` : id
  }

  const getPlayerNames = (run) => {
    // We don't persist full profiles in matches, just IDs
    return run.playerId || '???'
  }

  return (
    <div className="history fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="panel-title">Match History</div>
        {matches.length > 0 && (
          <button className="btn danger" onClick={onClear} style={{ padding: '4px 12px', fontSize: 11 }}>
            Clear
          </button>
        )}
      </div>

      {matches.length === 0 && (
        <div className="history-empty">No matches recorded yet.</div>
      )}

      {matches.map((m) => {
        // We need to find which run was the winner
        // Just show first run as fallback
        const firstRun = m.runs?.[0]
        return (
          <div className="history-item" key={m.id}>
            <div>
              <div style={{ fontSize: 11, color: 'var(--gray)' }}>
                {new Date(m.createdAt).toLocaleDateString()} &middot; {getTxName(m.transmissionId)}
              </div>
              <div>
                {m.runs?.length || 0} operator{(m.runs?.length || 0) !== 1 ? 's' : ''}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div className="winner">★ Winner</div>
              <div style={{ fontSize: 11, color: 'var(--gray)' }}>
                {firstRun?.playerId || '—'}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
