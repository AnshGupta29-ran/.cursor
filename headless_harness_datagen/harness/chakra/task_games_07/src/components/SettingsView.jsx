export default function SettingsView({ settings, onUpdate }) {
  return (
    <div className="settings fade-in">
      <div className="panel-title">Settings</div>

      <div className="setting-row">
        <label>Ghost Replay Speed</label>
        <select
          value={settings.ghostSpeed}
          onChange={(e) => onUpdate({ ghostSpeed: parseFloat(e.target.value) })}
        >
          <option value={0.5}>0.5×</option>
          <option value={1}>1×</option>
          <option value={2}>2×</option>
        </select>
      </div>

      <div className="setting-row">
        <label>Default Length Class</label>
        <select
          value={settings.lengthClass}
          onChange={(e) => onUpdate({ lengthClass: e.target.value })}
        >
          <option value="short">Short</option>
          <option value="standard">Standard</option>
          <option value="burst">Burst</option>
        </select>
      </div>

      <div className="setting-row">
        <label>Time Cap</label>
        <select
          value={settings.timeCapSec}
          onChange={(e) => onUpdate({ timeCapSec: parseInt(e.target.value, 10) })}
        >
          <option value={45}>45 seconds</option>
          <option value={60}>60 seconds</option>
          <option value={90}>90 seconds</option>
        </select>
      </div>

      <div className="setting-row">
        <label>Sound Effects (muted)</label>
        <input
          type="checkbox"
          checked={settings.muted}
          onChange={(e) => onUpdate({ muted: e.target.checked })}
        />
      </div>
    </div>
  )
}
