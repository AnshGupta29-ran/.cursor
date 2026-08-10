import { useMemo, useState } from "react";
import { api } from "../api";
import type { Device, Schedule } from "../types";

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

interface Props {
  devices: Device[];
  schedules: Schedule[];
  refresh: () => void;
}

export default function Schedules({ devices, schedules, refresh }: Props) {
  const [deviceId, setDeviceId] = useState("");
  const [time, setTime] = useState("07:30");
  const [days, setDays] = useState<number[]>([0, 1, 2, 3, 4, 5, 6]);
  const [actionJson, setActionJson] = useState('{"is_on": true}');
  const [error, setError] = useState("");

  const deviceName = useMemo(() => {
    const map = new Map(devices.map((d) => [d.id, d.name]));
    return (id: string) => map.get(id) ?? "Unknown device";
  }, [devices]);

  const toggleDay = (d: number) =>
    setDays((prev) => (prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d].sort()));

  const submit = async () => {
    setError("");
    if (!deviceId) return setError("Pick a device");
    let action: Record<string, unknown>;
    try {
      action = JSON.parse(actionJson);
      if (typeof action !== "object" || action === null || Array.isArray(action))
        throw new Error();
    } catch {
      return setError('Action must be a JSON object, e.g. {"is_on": true, "brightness": 60}');
    }
    try {
      await api.createSchedule({ device_id: deviceId, time, action, days, enabled: true });
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create schedule");
    }
  };

  return (
    <div className="panel">
      <h2>Schedules</h2>
      <p className="muted">
        Run a device action at a set time on chosen days. Actions use the same state fields as
        device control.
      </p>

      <div className="form">
        <select value={deviceId} onChange={(e) => setDeviceId(e.target.value)}>
          <option value="">Select device…</option>
          {devices.map((d) => (
            <option key={d.id} value={d.id}>
              {d.room} · {d.name}
            </option>
          ))}
        </select>
        <input type="time" value={time} onChange={(e) => setTime(e.target.value)} />
        <div className="segmented days">
          {DAY_LABELS.map((label, i) => (
            <button
              key={label}
              className={days.includes(i) ? "seg active" : "seg"}
              onClick={() => toggleDay(i)}
            >
              {label}
            </button>
          ))}
        </div>
        <input
          className="mono"
          value={actionJson}
          onChange={(e) => setActionJson(e.target.value)}
          placeholder='{"is_on": true}'
        />
        <button onClick={submit}>Add schedule</button>
        {error && <div className="error">{error}</div>}
      </div>

      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Device</th>
            <th>Days</th>
            <th>Action</th>
            <th>Enabled</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {schedules.map((s) => (
            <tr key={s.id}>
              <td className="mono">{s.time}</td>
              <td>{deviceName(s.device_id)}</td>
              <td>
                {s.days.length === 7 || s.days.length === 0
                  ? "Every day"
                  : s.days.map((d) => DAY_LABELS[d]).join(" ")}
              </td>
              <td className="mono small">{JSON.stringify(s.action)}</td>
              <td>
                <input
                  type="checkbox"
                  checked={s.enabled}
                  onChange={async (e) => {
                    await api.updateSchedule(s.id, { enabled: e.target.checked });
                    refresh();
                  }}
                />
              </td>
              <td>
                <button
                  className="danger"
                  onClick={async () => {
                    await api.deleteSchedule(s.id);
                    refresh();
                  }}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
          {schedules.length === 0 && (
            <tr>
              <td colSpan={6} className="muted">
                No schedules yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
