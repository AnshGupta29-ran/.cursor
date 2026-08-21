import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api } from '../api.js';
import { Card, Loading, ErrorBox, Empty, VerdictChip, btn } from '../components.jsx';

export default function ExperimentDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const [exp, setExp] = useState(null);
  const [influence, setInfluence] = useState(null);
  const [verdicts, setVerdicts] = useState({});
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState([]);

  const load = async () => {
    try {
      const e = await api.getExperiment(id);
      setExp(e);
      const inf = await api.getInfluence(id);
      setInfluence(inf);
      // fetch verdicts for finished runs
      const v = {};
      for (const r of e.run_objects || []) {
        if (r.status === 'FINISHED') {
          try { v[r.id] = await api.getVerdict(r.id); } catch {}
        }
      }
      setVerdicts(v);
    } catch (e) { setError(e); }
  };
  useEffect(() => { load(); }, [id]);

  if (error) return <ErrorBox error={error} />;
  if (!exp) return <Loading />;

  const champion = (exp.run_objects || []).find(r => r.id === exp.champion_run_id);
  const toggle = (rid) => {
    setSelected(s => s.includes(rid) ? s.filter(x => x !== rid) : (s.length < 4 ? [...s, rid] : s));
  };

  const lastVal = (r, m) => {
    const s = r.metrics?.[m];
    return s && s.length ? s[s.length - 1].value : null;
  };
  const primary = exp.gate_policy?.primary_metric || 'f1';

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
        <Link to="/experiments" style={{ color: '#2563eb', textDecoration: 'none', fontSize: 13 }}>← Experiments</Link>
      </div>
      <h2 style={{ margin: '4px 0 4px' }}>{exp.name}</h2>
      <p style={{ color: '#7c8698', fontSize: 13, marginTop: 0 }}>
        Gate: <code>{primary}</code> must improve by ≥ {exp.gate_policy?.min_delta_pct}%
        {exp.gate_policy?.guard_metric && (
          <> while <code>{exp.gate_policy.guard_metric}</code> may regress at most {exp.gate_policy.guard_max_regress_pct}%</>
        )}
      </p>

      {champion ? (
        <div style={{
          background: 'linear-gradient(90deg,#10192b,#1d2d4a)', color: '#fff',
          borderRadius: 10, padding: 16, marginBottom: 18, display: 'flex', alignItems: 'center', gap: 14,
        }}>
          <span style={{ fontSize: 26 }}>🏆</span>
          <div>
            <div style={{ fontWeight: 700 }}>Champion: {champion.name}</div>
            <div style={{ fontSize: 13, color: '#b9c6dc' }}>
              {primary} = {lastVal(champion, primary)?.toFixed(4)} · lr {champion.params?.learning_rate} · batch {champion.params?.batch_size}
            </div>
          </div>
          <div style={{ marginLeft: 'auto' }}>
            <button style={btn.ghost} onClick={() => nav(`/experiments/${id}/compare?run_ids=${selected.join(',')}`)} disabled={selected.length === 0}>
              Compare selected ({selected.length})
            </button>
          </div>
        </div>
      ) : (
        <Card>
          <Empty>No champion pinned — verdicts will be INCONCLUSIVE until you pin one.</Empty>
        </Card>
      )}

      <Card title={`Runs (${(exp.run_objects || []).length})`}>
        {(exp.run_objects || []).length === 0 ? <Empty>No runs yet. Log one via the API.</Empty> : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ textAlign: 'left', color: '#5b6472', borderBottom: '1px solid #e4e9f2' }}>
                <th style={th}></th>
                <th style={th}>Run</th>
                <th style={th}>Status</th>
                <th style={th}>{primary}</th>
                <th style={th}>Verdict</th>
                <th style={th}>Key params</th>
                <th style={th}></th>
              </tr>
            </thead>
            <tbody>
              {(exp.run_objects || []).map(r => (
                <tr key={r.id} style={{ borderBottom: '1px solid #f0f2f7', background: r.id === exp.champion_run_id ? '#fffbe9' : 'transparent' }}>
                  <td style={td}>
                    <input type="checkbox" checked={selected.includes(r.id)} onChange={() => toggle(r.id)} />
                  </td>
                  <td style={td}>
                    <Link to={`/runs/${r.id}`} style={{ color: '#2563eb', textDecoration: 'none', fontWeight: 600 }}>
                      {r.name}
                    </Link>
                    {r.id === exp.champion_run_id && <span style={{ marginLeft: 6 }}>🏆</span>}
                  </td>
                  <td style={td}><StatusPill s={r.status} /></td>
                  <td style={td}>{lastVal(r, primary)?.toFixed(4) ?? '—'}</td>
                  <td style={td}>
                    {verdicts[r.id] ? <VerdictChip verdict={verdicts[r.id].verdict} /> : '—'}
                  </td>
                  <td style={{ ...td, color: '#5b6472' }}>
                    {Object.entries(r.params || {}).slice(0, 3).map(([k, v]) => `${k}=${v}`).join(' · ')}
                  </td>
                  <td style={td}>
                    {r.id !== exp.champion_run_id ? (
                      <button style={btn.ghost} onClick={async () => { await api.setChampion(id, r.id); load(); }}>
                        Pin champion
                      </button>
                    ) : (
                      <button style={btn.danger} onClick={async () => { await api.deleteRun(id, r.id); load(); }}>
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <Card title="Parameter influence — what moved the needle?">
        {!influence ? <Loading /> : influence.drivers.length === 0 ? (
          <Empty>{influence.message}</Empty>
        ) : (
          <ol style={{ margin: 0, paddingLeft: 20 }}>
            {influence.drivers.map(d => (
              <li key={d.param} style={{ marginBottom: 8, fontSize: 14 }}>
                <strong>{d.param}</strong> <span style={{ color: '#7c8698' }}>(r = {d.correlation})</span>
                <div style={{ color: '#39465c' }}>{d.explanation}</div>
              </li>
            ))}
          </ol>
        )}
      </Card>
    </div>
  );
}

function StatusPill({ s }) {
  const map = {
    RUNNING: { bg: '#e0ecff', fg: '#1d4ed8' },
    FINISHED: { bg: '#d9f7e3', fg: '#0b6b2f' },
    FAILED: { bg: '#fde2e1', fg: '#a02121' },
  };
  const c = map[s] || map.RUNNING;
  return <span style={{ background: c.bg, color: c.fg, padding: '2px 8px', borderRadius: 12, fontSize: 11, fontWeight: 700 }}>{s}</span>;
}

const th = { padding: '8px 10px', fontWeight: 600, fontSize: 12 };
const td = { padding: '9px 10px' };
