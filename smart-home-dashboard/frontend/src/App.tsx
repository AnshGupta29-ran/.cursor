import { useState } from "react";
import { useSmartHome } from "./hooks/useSmartHome";
import Dashboard from "./components/Dashboard";
import Schedules from "./components/Schedules";
import Rules from "./components/Rules";
import History from "./components/History";

type Tab = "dashboard" | "schedules" | "rules" | "history";

const TABS: { id: Tab; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "schedules", label: "Schedules" },
  { id: "rules", label: "Automation Rules" },
  { id: "history", label: "History" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const home = useSmartHome();

  return (
    <div className="app">
      <header className="topbar">
        <h1>Smart Home</h1>
        <nav>
          {TABS.map((t) => (
            <button
              key={t.id}
              className={tab === t.id ? "tab active" : "tab"}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
        <span
          className={home.connected ? "conn connected" : "conn"}
          title={home.connected ? "Live updates connected" : "Reconnecting…"}
        >
          {home.connected ? "● Live" : "○ Offline"}
        </span>
      </header>

      <main>
        {tab === "dashboard" && (
          <Dashboard
            devices={home.devices}
            control={home.control}
            refreshDevices={home.refreshDevices}
          />
        )}
        {tab === "schedules" && (
          <Schedules
            devices={home.devices}
            schedules={home.schedules}
            refresh={home.refreshSchedules}
          />
        )}
        {tab === "rules" && (
          <Rules devices={home.devices} rules={home.rules} refresh={home.refreshRules} />
        )}
        {tab === "history" && <History devices={home.devices} />}
      </main>

      <div className="toasts">
        {home.toasts.map((t) => (
          <div key={t.id} className="toast">
            {t.text}
          </div>
        ))}
      </div>
    </div>
  );
}
