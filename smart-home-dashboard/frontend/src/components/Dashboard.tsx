import { useMemo, useState } from "react";
import { api } from "../api";
import type { Device, DeviceType } from "../types";
import DeviceCard from "./DeviceCard";

interface Props {
  devices: Device[];
  control: (deviceId: string, state: Record<string, unknown>) => void;
  refreshDevices: () => void;
}

export default function Dashboard({ devices, control, refreshDevices }: Props) {
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const [room, setRoom] = useState("");
  const [type, setType] = useState<DeviceType>("light");

  const byRoom = useMemo(() => {
    const map = new Map<string, Device[]>();
    for (const d of devices) {
      const list = map.get(d.room) ?? [];
      list.push(d);
      map.set(d.room, list);
    }
    return [...map.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [devices]);

  const addDevice = async () => {
    if (!name.trim() || !room.trim()) return;
    await api.createDevice(name.trim(), room.trim(), type);
    setName("");
    setRoom("");
    setAdding(false);
    refreshDevices();
  };

  const summary = useMemo(() => {
    const lightsOn = devices.filter(
      (d) => d.type === "light" && (d.state as { is_on: boolean }).is_on
    ).length;
    const unlocked = devices.filter(
      (d) => d.type === "door" && !(d.state as { is_locked: boolean }).is_locked
    ).length;
    const motion = devices.filter(
      (d) => d.type === "camera" && (d.state as { motion_detected: boolean }).motion_detected
    ).length;
    return { lightsOn, unlocked, motion };
  }, [devices]);

  return (
    <div>
      <div className="summary">
        <span>💡 {summary.lightsOn} lights on</span>
        <span className={summary.unlocked ? "alert" : ""}>
          🔓 {summary.unlocked} doors unlocked
        </span>
        <span className={summary.motion ? "alert" : ""}>🚶 {summary.motion} motion events</span>
        <button className="add" onClick={() => setAdding((a) => !a)}>
          {adding ? "Cancel" : "+ Add device"}
        </button>
      </div>

      {adding && (
        <div className="add-form">
          <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
          <input placeholder="Room" value={room} onChange={(e) => setRoom(e.target.value)} />
          <select value={type} onChange={(e) => setType(e.target.value as DeviceType)}>
            <option value="light">Light</option>
            <option value="fan">Fan</option>
            <option value="thermostat">Thermostat</option>
            <option value="door">Door</option>
            <option value="camera">Camera</option>
          </select>
          <button onClick={addDevice}>Create</button>
        </div>
      )}

      {byRoom.map(([roomName, roomDevices]) => (
        <section key={roomName}>
          <h2>{roomName}</h2>
          <div className="grid">
            {roomDevices.map((d) => (
              <DeviceCard key={d.id} device={d} control={control} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
