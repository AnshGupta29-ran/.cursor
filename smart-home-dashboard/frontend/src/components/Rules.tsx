import { useMemo, useState } from "react";
import { api } from "../api";
import type { Device, Metric, Operator, Rule } from "../types";

const METRICS: { value: Metric; label: string }[] = [
  { value: "temperature", label: "Temperature (°C)" },
  { value: "humidity", label: "Humidity (%)" },
  { value: "motion", label: "Motion (0/1)" },
];

interface Props {
  devices: Device[];
  rules: Rule[];
  refresh: () => void;
}

export default function Rules({ devices, rules, refresh }: Props) {
  const [name, setName] = useState("");
  const [sourceId, setSourceId] = useState("");
  const [metric, setMetric] = useState<Metric>("temperature");
  const [operator, setOperator] = useState<Operator>("gt");
  const [threshold, setThreshold] = useState("26");
  const [targetId, setTargetId] = useState("");
  const [actionJson, setActionJson] = useState('{"is_on": true}');
  const [error, setError] = useState("");

  const sensors = useMemo(
    () => devices.filter((d) => d.type === "thermostat" || d.type === "camera"),
    [devices]
  );
  const deviceName = useMemo(() => {
    const map = new Map(devices.map((d) => [d.id, d.name]));
    return (id: string) => map.get(id) ?? "Unknown";
  }, [devices]);

  const submit = async () => {
    setError("");
    if (!name.trim() || !sourceId || !targetId) return setError("Fill in all fields");
    let action: Record<string, unknown>;
    try {
      action = JSON.parse(actionJson);
      if (typeof action !== "object" || action === null || Array.isArray(action))
        throw new Error();
    } catch {
      return setError('Action must be a JSON object, e.g. {"is_on": true, "speed": 3}');
    }
    try {
      await api.createRule({
        name: name.trim(),
        source_device_id: sourceId,
        metric,
        operator,
        threshold: Number(threshold),
        target_device_id: targetId,
        action,
        enabled: true,
      });
      setName("");
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create rule");
    }
  };

  return (
    <div className="panel">
      <h2>Automation Rules</h2>
      <p className="muted">
        WHEN a sensor crosses a threshold, THEN apply an action to a device. Rules fire once per
        crossing and re-arm when the sensor returns to normal.
      </p>

      <div className="form">
        <input placeholder="Rule name" value={name} onChange={(e) => setName(e.target.value)} />
        <div className="form-row">
          <span className="muted">WHEN</span>
          <select value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
            <option value="">Sensor…</option>
            {sensors.map((d) => (
              <option key={d.id} value={d.id}>
                {d.room} · {d.name}
              </option>
            ))}
          </select>
          <select value={metric} onChange={(e) => setMetric(e.target.value as Metric)}>
            {METRICS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
          <select value={operator} onChange={(e) => setOperator(e.target.value as Operator)}>
            <option value="gt">goes above</option>
            <option value="lt">drops below</option>
          </select>
          <input
            type="number"
            step="0.5"
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
            style={{ width: 90 }}
          />
        </div>
        <div className="form-row">
          <span className="muted">THEN</span>
          <select value={targetId} onChange={(e) => setTargetId(e.target.value)}>
            <option value="">Device…</option>
            {devices.map((d) => (
              <option key={d.id} value={d.id}>
                {d.room} · {d.name}
              </option>
            ))}
          </select>
          <input
            className="mono grow"
            value={actionJson}
            onChange={(e) => setActionJson(e.target.value)}
            placeholder='{"is_on": true}'
          />
        </div>
        <button onClick={submit}>Add rule</button>
        {error && <div className="error">{error}</div>}
      </div>

      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Condition</th>
            <th>Action</th>
            <th>State</th>
            <th>Enabled</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {rules.map((r) => (
            <tr key={r.id}>
              <td>{r.name}</td>
              <td>
                {deviceName(r.source_device_id)} {r.metric} {r.operator === "gt" ? ">" : "<"}{" "}
                {r.threshold}
              </td>
              <td>
                {deviceName(r.target_device_id)}{" "}
                <span className="mono small">{JSON.stringify(r.action)}</span>
              </td>
              <td>
                <span className={r.triggered ? "chip fired" : "chip"}>
                  {r.triggered ? "Fired" : "Armed"}
                </span>
              </td>
              <td>
                <input
                  type="checkbox"
                  checked={r.enabled}
                  onChange={async (e) => {
                    await api.updateRule(r.id, { enabled: e.target.checked });
                    refresh();
                  }}
                />
              </td>
              <td>
                <button
                  className="danger"
                  onClick={async () => {
                    await api.deleteRule(r.id);
                    refresh();
                  }}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
          {rules.length === 0 && (
            <tr>
              <td colSpan={6} className="muted">
                No rules yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
