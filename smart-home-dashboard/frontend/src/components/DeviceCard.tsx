import type { ReactElement } from "react";
import type {
  CameraState,
  Device,
  DoorState,
  FanState,
  LightState,
  ThermostatState,
} from "../types";

const ICONS: Record<Device["type"], string> = {
  light: "💡",
  fan: "🌀",
  thermostat: "🌡️",
  door: "🚪",
  camera: "📷",
};

interface Props {
  device: Device;
  control: (deviceId: string, state: Record<string, unknown>) => void;
}

export default function DeviceCard({ device, control }: Props) {
  const send = (state: Record<string, unknown>) => control(device.id, state);
  const s = device.state;

  let body: ReactElement;
  switch (device.type) {
    case "light": {
      const st = s as LightState;
      body = (
        <>
          <button className={st.is_on ? "toggle on" : "toggle"} onClick={() => send({ is_on: !st.is_on })}>
            {st.is_on ? "On" : "Off"}
          </button>
          <label>
            Brightness {st.brightness}%
            <input
              type="range" min={0} max={100} value={st.brightness}
              onChange={(e) => send({ brightness: Number(e.target.value) })}
            />
          </label>
          <label>
            Warmth {st.color_temp_k}K
            <input
              type="range" min={2200} max={6500} step={100} value={st.color_temp_k}
              onChange={(e) => send({ color_temp_k: Number(e.target.value) })}
            />
          </label>
        </>
      );
      break;
    }
    case "fan": {
      const st = s as FanState;
      body = (
        <>
          <button className={st.is_on ? "toggle on" : "toggle"} onClick={() => send({ is_on: !st.is_on })}>
            {st.is_on ? "On" : "Off"}
          </button>
          <div className="segmented">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                className={st.speed === n && st.is_on ? "seg active" : "seg"}
                onClick={() => send({ is_on: true, speed: n })}
              >
                {n}
              </button>
            ))}
          </div>
        </>
      );
      break;
    }
    case "thermostat": {
      const st = s as ThermostatState;
      body = (
        <>
          <div className="temp-display">
            {st.current_temp_c.toFixed(1)}°C
            <span className="muted"> · {st.humidity_pct.toFixed(0)}% RH</span>
          </div>
          <label>
            Target {st.target_temp_c.toFixed(1)}°C
            <input
              type="range" min={10} max={32} step={0.5} value={st.target_temp_c}
              onChange={(e) => send({ target_temp_c: Number(e.target.value) })}
            />
          </label>
          <div className="segmented">
            {(["heat", "cool", "auto", "off"] as const).map((m) => (
              <button
                key={m}
                className={st.mode === m ? "seg active" : "seg"}
                onClick={() => send({ mode: m })}
              >
                {m}
              </button>
            ))}
          </div>
        </>
      );
      break;
    }
    case "door": {
      const st = s as DoorState;
      body = (
        <div className="door-grid">
          <button className={st.is_open ? "toggle warn" : "toggle"} onClick={() => send({ is_open: !st.is_open })}>
            {st.is_open ? "Open" : "Closed"}
          </button>
          <button
            className={st.is_locked ? "toggle on" : "toggle warn"}
            onClick={() => send({ is_locked: !st.is_locked })}
          >
            {st.is_locked ? "Locked" : "Unlocked"}
          </button>
        </div>
      );
      break;
    }
    case "camera": {
      const st = s as CameraState;
      const offline = st.status === "offline";
      body = (
        <>
          <div className="camera-status">
            <span className={st.motion_detected ? "motion active" : "motion"}>
              {st.motion_detected ? "Motion detected" : "No motion"}
            </span>
            <span className={st.is_recording ? "rec" : "muted"}>
              {st.is_recording ? "● REC" : "Not recording"}
            </span>
          </div>
          <div className="door-grid">
            <button
              className={st.is_recording ? "toggle on" : "toggle"}
              disabled={offline}
              onClick={() => send({ is_recording: !st.is_recording })}
            >
              {st.is_recording ? "Recording" : "Record"}
            </button>
            <button
              className={offline ? "toggle warn" : "toggle"}
              onClick={() => send({ status: offline ? "online" : "offline" })}
            >
              {offline ? "Offline" : "Online"}
            </button>
          </div>
        </>
      );
      break;
    }
  }

  return (
    <div className={`card ${device.type}`}>
      <div className="card-head">
        <span className="icon">{ICONS[device.type]}</span>
        <div>
          <div className="card-title">{device.name}</div>
          <div className="muted small">{device.room}</div>
        </div>
      </div>
      <div className="card-body">{body}</div>
    </div>
  );
}
