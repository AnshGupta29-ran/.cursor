import { useEffect, useMemo, useState } from "react";
import {
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api";
import type { Device, Reading } from "../types";

interface Props {
  devices: Device[];
}

interface Point {
  time: string;
  temperature?: number;
  humidity?: number;
  power?: number;
  motion?: number;
}

export default function History({ devices }: Props) {
  const [deviceId, setDeviceId] = useState("");
  const [readings, setReadings] = useState<Reading[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (devices.length && !deviceId) {
      const firstSensor =
        devices.find((d) => d.type === "thermostat") ?? devices[0];
      setDeviceId(firstSensor.id);
    }
  }, [devices, deviceId]);

  useEffect(() => {
    if (!deviceId) return;
    setLoading(true);
    api
      .history(deviceId)
      .then(setReadings)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [deviceId]);

  const points: Point[] = useMemo(
    () =>
      readings.map((r) => ({
        time: new Date(r.ts * 1000).toLocaleTimeString(),
        temperature: r.temperature_c ?? undefined,
        humidity: r.humidity_pct ?? undefined,
        power: r.power_w ?? undefined,
        motion: r.motion ?? undefined,
      })),
    [readings]
  );

  const device = devices.find((d) => d.id === deviceId);
  const hasTemp = points.some((p) => p.temperature !== undefined);
  const hasMotion = points.some((p) => p.motion !== undefined);

  return (
    <div className="panel">
      <h2>Sensor History</h2>
      <div className="form-row">
        <select value={deviceId} onChange={(e) => setDeviceId(e.target.value)}>
          {devices.map((d) => (
            <option key={d.id} value={d.id}>
              {d.room} · {d.name} ({d.type})
            </option>
          ))}
        </select>
        <button
          onClick={() => {
            setLoading(true);
            api.history(deviceId).then(setReadings).finally(() => setLoading(false));
          }}
        >
          Refresh
        </button>
      </div>

      {loading && <p className="muted">Loading…</p>}
      {!loading && points.length === 0 && (
        <p className="muted">
          No readings yet — the simulator records one per tick (every ~5s) while the backend is
          running.
        </p>
      )}

      {points.length > 0 && (
        <div className="chart">
          <ResponsiveContainer width="100%" height={360}>
            <LineChart data={points} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
              <XAxis dataKey="time" tick={{ fontSize: 11 }} minTickGap={40} />
              <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              {hasTemp && (
                <>
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="temperature"
                    stroke="#f97316"
                    dot={false}
                    name="Temp °C"
                  />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="humidity"
                    stroke="#3b82f6"
                    dot={false}
                    name="Humidity %"
                  />
                </>
              )}
              {hasMotion && (
                <Line
                  yAxisId="left"
                  type="stepAfter"
                  dataKey="motion"
                  stroke="#ef4444"
                  dot={false}
                  name="Motion"
                />
              )}
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="power"
                stroke="#22c55e"
                dot={false}
                name="Power W"
              />
            </LineChart>
          </ResponsiveContainer>
          {device && (
            <p className="muted small">
              {points.length} readings for {device.name}. Thermostats record temperature,
              humidity and power; cameras record motion; lights and fans record power.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
