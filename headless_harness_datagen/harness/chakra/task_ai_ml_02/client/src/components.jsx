import React from 'react';

export function VerdictChip({ verdict }) {
  const map = {
    PASS: { bg: '#d9f7e3', fg: '#0b6b2f', label: 'PASS' },
    REGRESSED: { bg: '#fde2e1', fg: '#a02121', label: 'REGRESSED' },
    INCONCLUSIVE: { bg: '#f0f1f5', fg: '#5b6472', label: 'INCONCLUSIVE' },
  };
  const c = map[verdict] || map.INCONCLUSIVE;
  return (
    <span style={{
      background: c.bg, color: c.fg, padding: '3px 10px', borderRadius: 14,
      fontWeight: 700, fontSize: 12, letterSpacing: 0.4,
    }}>
      {c.label}
    </span>
  );
}

export function Card({ title, children, actions }) {
  return (
    <div style={{
      background: '#fff', borderRadius: 10, padding: 18, marginBottom: 18,
      boxShadow: '0 1px 3px rgba(16,25,43,0.08)',
    }}>
      {(title || actions) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <h3 style={{ margin: 0, fontSize: 16 }}>{title}</h3>
          <div>{actions}</div>
        </div>
      )}
      {children}
    </div>
  );
}

export function Loading() {
  return <div style={{ padding: 40, textAlign: 'center', color: '#7c8698' }}>Loading…</div>;
}

export function ErrorBox({ error }) {
  if (!error) return null;
  return (
    <div style={{
      background: '#fde2e1', color: '#a02121', padding: 14, borderRadius: 8,
      marginBottom: 16, fontSize: 14,
    }}>
      <strong>{error.code || 'error'}:</strong> {error.message}
    </div>
  );
}

export function Empty({ children }) {
  return (
    <div style={{ padding: 24, textAlign: 'center', color: '#7c8698', fontSize: 14 }}>
      {children}
    </div>
  );
}

/** Hand-rolled SVG line chart for one metric across runs. */
export function MetricChart({ series, notes = [], height = 220, width = 640 }) {
  if (!series || series.length === 0) return <Empty>No metric data</Empty>;
  // series: [{label, color, points:[{step,value}]}]
  const allPoints = series.flatMap(s => s.points);
  const xs = allPoints.map(p => p.step);
  const ys = allPoints.map(p => p.value);
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const yMin = Math.min(...ys), yMax = Math.max(...ys);
  const pad = 34;
  const sx = x => pad + ((x - xMin) / (xMax - xMin || 1)) * (width - pad * 2);
  const sy = y => height - pad - ((y - yMin) / (yMax - yMin || 1)) * (height - pad * 2);
  const colors = ['#2563eb', '#16a34a', '#dc2626', '#9333ea'];
  return (
    <div>
      <svg width={width} height={height} style={{ background: '#fbfcfe', borderRadius: 8, border: '1px solid #e4e9f2' }}>
        {[0.25, 0.5, 0.75].map(f => (
          <line key={f} x1={pad} x2={width - pad} y1={pad + f * (height - pad * 2)} y2={pad + f * (height - pad * 2)} stroke="#eef1f6" />
        ))}
        {series.map((s, i) => (
          <polyline
            key={i}
            fill="none"
            stroke={s.color || colors[i % colors.length]}
            strokeWidth={2}
            points={s.points.map(p => `${sx(p.step)},${sy(p.value)}`).join(' ')}
          />
        ))}
        {series.map((s, i) =>
          s.points.map((p, j) => (
            <circle key={`${i}-${j}`} cx={sx(p.step)} cy={sy(p.value)} r={2.5} fill={s.color || colors[i % colors.length]} />
          ))
        )}
        <text x={pad} y={14} fontSize={11} fill="#5b6472">{yMax.toFixed(4)}</text>
        <text x={pad} y={height - 6} fontSize={11} fill="#5b6472">{yMin.toFixed(4)}</text>
        <text x={width - pad - 40} y={height - 6} fontSize={11} fill="#5b6472">step {xMax}</text>
      </svg>
      <div style={{ display: 'flex', gap: 14, marginTop: 6, flexWrap: 'wrap' }}>
        {series.map((s, i) => (
          <span key={i} style={{ fontSize: 12, color: '#5b6472' }}>
            <span style={{ color: s.color || colors[i % colors.length] }}>●</span> {s.label}
          </span>
        ))}
      </div>
      {notes.length > 0 && (
        <div style={{ marginTop: 8 }}>
          {notes.map((n, i) => (
            <span key={i} style={{
              display: 'inline-block', background: '#fff4d6', color: '#8a6d1f',
              border: '1px solid #ecd27f', borderRadius: 6, padding: '3px 8px',
              fontSize: 12, marginRight: 6, marginTop: 4,
            }}>
              ⚠ {n}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export const btn = {
  primary: {
    background: '#2563eb', color: '#fff', border: 'none', borderRadius: 8,
    padding: '8px 14px', cursor: 'pointer', fontSize: 14, fontWeight: 600,
  },
  ghost: {
    background: 'transparent', color: '#2563eb', border: '1px solid #c7d4ea',
    borderRadius: 8, padding: '7px 12px', cursor: 'pointer', fontSize: 13,
  },
  danger: {
    background: 'transparent', color: '#a02121', border: '1px solid #ecc',
    borderRadius: 8, padding: '6px 10px', cursor: 'pointer', fontSize: 12,
  },
};
