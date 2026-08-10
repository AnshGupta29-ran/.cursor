export type DeviceType = "light" | "fan" | "thermostat" | "door" | "camera";

export interface LightState {
  is_on: boolean;
  brightness: number;
  color_temp_k: number;
}
export interface FanState {
  is_on: boolean;
  speed: number;
}
export interface ThermostatState {
  current_temp_c: number;
  target_temp_c: number;
  humidity_pct: number;
  mode: "heat" | "cool" | "auto" | "off";
}
export interface DoorState {
  is_open: boolean;
  is_locked: boolean;
}
export interface CameraState {
  is_recording: boolean;
  motion_detected: boolean;
  status: "online" | "offline";
}

export type DeviceState =
  | LightState
  | FanState
  | ThermostatState
  | DoorState
  | CameraState;

export interface Device {
  id: string;
  name: string;
  room: string;
  type: DeviceType;
  state: DeviceState;
  updated_at: number;
}

export interface Schedule {
  id: string;
  device_id: string;
  time: string;
  action: Record<string, unknown>;
  days: number[];
  enabled: boolean;
}

export type Metric = "temperature" | "humidity" | "motion";
export type Operator = "gt" | "lt";

export interface Rule {
  id: string;
  name: string;
  source_device_id: string;
  metric: Metric;
  operator: Operator;
  threshold: number;
  target_device_id: string;
  action: Record<string, unknown>;
  enabled: boolean;
  triggered: boolean;
}

export interface Reading {
  ts: number;
  device_id: string;
  temperature_c: number | null;
  humidity_pct: number | null;
  power_w: number | null;
  motion: number | null;
}

export type WsEvent =
  | { type: "snapshot"; data: Device[] }
  | { type: "device_updated"; data: Device }
  | { type: "rule_triggered"; data: Rule };
