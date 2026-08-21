import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api.js';
import { Card, Loading, ErrorBox, Empty, btn } from '../components.jsx';

export default function Experiments() {
  const [exps, setExps] = useState(null);
  const [error, setError] = useState(null);
  const [name, setName] = useState('');
  const [seeding, setSeeding] = useState(false);
  const nav = useNavigate();

  const load = () => {
    api.listExperiments().then(setExps).catch(e => setError(e));
  };
  useEffect(load, []);

  const seed = async () => {
    setSeeding(true);
    setError(null);
    try {
      const r = await api.seed();
      nav(`/experiments/${r.experiment_id}`);
    } catch (e) { setError(e); setSeeding(false); }
  };

  const create = async (ev) => {
    ev.preventDefault();
    if (!name.trim()) return;
    try {
      const e = await api.createExperiment(name.trim());
      setName('');
      nav(`/experiments/${e.id}`);
    } catch (e) { setError(e); }
  };

  if (error && !exps) return <ErrorBox error={error} />;
  if (!exps) return <Loading />;

  return (
    <div>
      <ErrorBox error={error} />
      <Card
        title="Experiments"
        actions={
          <button style={btn.primary} onClick={seed} disabled={seeding}>
            {seeding ? 'Seeding…' : 'Seed demo: sentiment-sweep'}
          </button>
        }
      >
        {exps.length === 0 ? (
          <Empty>
            No experiments yet. Click <strong>Seed demo</strong> to load 8 deterministic
            sweep runs with a pinned champion, or create one below.
          </Empty>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ textAlign: 'left', color: '#5b6472', borderBottom: '1px solid #e4e9f2' }}>
                <th style={th}>Name</th>
                <th style={th}>Runs</th>
                <th style={th}>Champion</th>
                <th style={th}>Gate</th>
                <th style={th}>Created</th>
              </tr>
            </thead>
            <tbody>
              {exps.map(e => (
                <tr key={e.id} style={{ borderBottom: '1px solid #f0f2f7' }}>
                  <td style={td}>
                    <Link to={`/experiments/${e.id}`} style={{ color: '#2563eb', fontWeight: 600, textDecoration: 'none' }}>
                      {e.name}
                    </Link>
                  </td>
                  <td style={td}>{e.run_count}</td>
                  <td style={td}>{e.champion_run_id ? '🏆 pinned' : '—'}</td>
                  <td style={td}>
                    {e.gate_policy?.primary_metric} +{e.gate_policy?.min_delta_pct}%
                  </td>
                  <td style={td}>{new Date(e.created_at * 1000).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <Card title="New experiment">
        <form onSubmit={create} style={{ display: 'flex', gap: 10 }}>
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="e.g. toxicity-bert-sweep"
            style={{ flex: 1, padding: '8px 12px', borderRadius: 8, border: '1px solid #c7d4ea', fontSize: 14 }}
          />
          <button type="submit" style={btn.primary}>Create</button>
        </form>
        <p style={{ color: '#7c8698', fontSize: 12, marginTop: 8 }}>
          Default gate: primary metric <code>f1</code>, min improvement +0%. You can re-pin the champion with a custom policy later.
        </p>
      </Card>
    </div>
  );
}

const th = { padding: '8px 10px', fontWeight: 600, fontSize: 13 };
const td = { padding: '10px' };
