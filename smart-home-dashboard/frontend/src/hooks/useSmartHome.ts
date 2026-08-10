import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Device, Rule, Schedule, WsEvent } from "../types";

export interface Toast {
  id: number;
  text: string;
}

/** Central data hook: REST hydration + WebSocket live updates. */
export function useSmartHome() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [connected, setConnected] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toastId = useRef(0);

  const pushToast = useCallback((text: string) => {
    const id = ++toastId.current;
    setToasts((t) => [...t, { id, text }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000);
  }, []);

  const refreshDevices = useCallback(() => {
    api.listDevices().then(setDevices).catch(console.error);
  }, []);
  const refreshSchedules = useCallback(() => {
    api.listSchedules().then(setSchedules).catch(console.error);
  }, []);
  const refreshRules = useCallback(() => {
    api.listRules().then(setRules).catch(console.error);
  }, []);

  useEffect(() => {
    refreshDevices();
    refreshSchedules();
    refreshRules();
  }, [refreshDevices, refreshSchedules, refreshRules]);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let retry: ReturnType<typeof setTimeout> | undefined;
    let closed = false;

    const connect = () => {
      const proto = location.protocol === "https:" ? "wss" : "ws";
      ws = new WebSocket(`${proto}://${location.host}/ws`);
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        if (!closed) retry = setTimeout(connect, 2000);
      };
      ws.onerror = () => ws?.close();
      ws.onmessage = (msg) => {
        const event = JSON.parse(msg.data) as WsEvent;
        if (event.type === "snapshot") {
          setDevices(event.data);
        } else if (event.type === "device_updated") {
          setDevices((prev) =>
            prev.map((d) => (d.id === event.data.id ? event.data : d))
          );
        } else if (event.type === "rule_triggered") {
          pushToast(`Rule fired: ${event.data.name}`);
          setRules((prev) =>
            prev.map((r) => (r.id === event.data.id ? event.data : r))
          );
        }
      };
    };
    connect();
    return () => {
      closed = true;
      if (retry) clearTimeout(retry);
      ws?.close();
    };
  }, [pushToast]);

  const control = useCallback(
    async (deviceId: string, state: Record<string, unknown>) => {
      try {
        const updated = await api.controlDevice(deviceId, state);
        setDevices((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      } catch (err) {
        pushToast(err instanceof Error ? err.message : "Control failed");
      }
    },
    [pushToast]
  );

  return {
    devices,
    schedules,
    rules,
    connected,
    toasts,
    control,
    refreshDevices,
    refreshSchedules,
    refreshRules,
  };
}
