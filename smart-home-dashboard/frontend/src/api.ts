import type { Device, Metric, Operator, Reading, Rule, Schedule } from "./types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* keep statusText */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  listDevices: () => request<Device[]>("/devices"),
  controlDevice: (id: string, state: Record<string, unknown>) =>
    request<Device>(`/devices/${id}/control`, {
      method: "POST",
      body: JSON.stringify({ state }),
    }),
  createDevice: (name: string, room: string, type: string) =>
    request<Device>("/devices", {
      method: "POST",
      body: JSON.stringify({ name, room, type }),
    }),
  deleteDevice: (id: string) => request<void>(`/devices/${id}`, { method: "DELETE" }),

  listSchedules: () => request<Schedule[]>("/schedules"),
  createSchedule: (s: Omit<Schedule, "id">) =>
    request<Schedule>("/schedules", { method: "POST", body: JSON.stringify(s) }),
  updateSchedule: (id: string, patch: Partial<Schedule>) =>
    request<Schedule>(`/schedules/${id}`, { method: "PATCH", body: JSON.stringify(patch) }),
  deleteSchedule: (id: string) => request<void>(`/schedules/${id}`, { method: "DELETE" }),

  listRules: () => request<Rule[]>("/rules"),
  createRule: (r: {
    name: string;
    source_device_id: string;
    metric: Metric;
    operator: Operator;
    threshold: number;
    target_device_id: string;
    action: Record<string, unknown>;
    enabled: boolean;
  }) => request<Rule>("/rules", { method: "POST", body: JSON.stringify(r) }),
  updateRule: (id: string, patch: Partial<Rule>) =>
    request<Rule>(`/rules/${id}`, { method: "PATCH", body: JSON.stringify(patch) }),
  deleteRule: (id: string) => request<void>(`/rules/${id}`, { method: "DELETE" }),

  history: (deviceId: string, limit = 300) =>
    request<Reading[]>(`/history/${deviceId}?limit=${limit}`),
};
