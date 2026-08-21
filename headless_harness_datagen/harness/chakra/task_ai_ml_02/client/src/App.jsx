import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import Experiments from './pages/Experiments.jsx';
import ExperimentDetail from './pages/ExperimentDetail.jsx';
import Compare from './pages/Compare.jsx';
import RunDetail from './pages/RunDetail.jsx';
import Activity from './pages/Activity.jsx';

export default function App() {
  return (
    <Router>
      <div style={styles.shell}>
        <header style={styles.header}>
          <Link to="/experiments" style={styles.brand}>
            EpochLedger
          </Link>
          <span style={styles.tagline}>champion / challenger experiment journal</span>
          <nav style={styles.nav}>
            <Link to="/experiments" style={styles.navLink}>Experiments</Link>
            <Link to="/activity" style={styles.navLink}>API Activity</Link>
          </nav>
          <span style={styles.badge} title="All state lives in process memory and is wiped on restart">
            In-memory workspace — resets on restart
          </span>
        </header>
        <main style={styles.main}>
          <Routes>
            <Route path="/" element={<Navigate to="/experiments" replace />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/experiments/:id" element={<ExperimentDetail />} />
            <Route path="/experiments/:id/compare" element={<Compare />} />
            <Route path="/runs/:id" element={<RunDetail />} />
            <Route path="/activity" element={<Activity />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

const styles = {
  shell: { fontFamily: 'Inter, system-ui, sans-serif', color: '#1a2332', minHeight: '100vh', background: '#f4f6fa' },
  header: {
    display: 'flex', alignItems: 'center', gap: 14, padding: '12px 24px',
    background: '#10192b', color: '#fff', position: 'sticky', top: 0, zIndex: 10, flexWrap: 'wrap',
  },
  brand: { color: '#fff', fontWeight: 800, fontSize: 20, textDecoration: 'none', letterSpacing: 0.3 },
  tagline: { color: '#8fa3bf', fontSize: 13 },
  nav: { marginLeft: 'auto', display: 'flex', gap: 16 },
  navLink: { color: '#c9d6e8', textDecoration: 'none', fontSize: 14 },
  badge: {
    background: '#3d2e00', color: '#ffd76a', border: '1px solid #8a6d1f',
    padding: '4px 10px', borderRadius: 20, fontSize: 12, whiteSpace: 'nowrap',
  },
  main: { padding: 24, maxWidth: 1200, margin: '0 auto' },
};
