export default function Menu({ onSelect }) {
  return (
    <div className="menu">
      <div className="menu-title">Staticline</div>
      <div className="menu-sub">— Intercept Desk v1.0 —</div>
      <div className="menu-buttons">
        <button className="btn primary" onClick={() => onSelect('setup')}>
          New Match
        </button>
        <button className="btn" onClick={() => onSelect('demo')}>
          Demo Desk
        </button>
        <button className="btn" onClick={() => onSelect('history')}>
          History
        </button>
        <button className="btn" onClick={() => onSelect('settings')}>
          Settings
        </button>
      </div>
      <div style={{ color: '#557755', fontSize: 10, marginTop: 16, textAlign: 'center' }}>
        ⚡ 2–4 operators · ghost relay · one keyboard
      </div>
    </div>
  )
}
