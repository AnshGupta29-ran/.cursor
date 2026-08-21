import React, { useEffect, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { api } from '../api.js';
import { Card, Loading, ErrorBox, Empty, VerdictChip, MetricChart } from '../components.jsx';

export default function Compare() {
  const { id } = useParams();
  const [sp] = useSearchParams();
  const runIds = (sp.get('run_ids') || '').split(',').filter(Boolean).slice(0, 4);
  const [data, setData] = useState(null);
  const [runs, setRuns] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const cmp = await api.compare(id, runIds);
        setData(cmp);
        const full = {};
        for (const rid of runIds) {
          full[rid] = await api.getRun(rid);
        }
        setRuns(full);
      } catch (e) { setError(e); }
    })();
  }, [id]);

  if (error) return <ErrorBox error={error} />;
  if (!data) return <Loading />;

  const metric = data.primary_metric;

  return (
    <div>
      <Link to={`/experiments/${id}`} style={{ color: '#2563eb', textDecoration: 'none', fontSize: 13 }}>← {data.experiment}</Link>
      <h2 style={{ margin: '6px 0 14px' }}>Compare runs</h2>

      {data.identical_configs && (
        <div style={{ background: '#fff4d6', border: '1px solid #ecd27f', borderRadius: 8, padding: 10, marginBottom: 14, fontSize: 13, color: '#8a6d1f' }}>
          These runs have identical configs — differences come from randomness only.
        </div>
      )}

      <Card title="Metric deltas vs champion">
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ textAlign: 'left', color: '#5b6472', borderBottom: '1px solid #e4e9f2' }}>
              <th style={th}>Run</th>
              <th style={th}>{metric}</th>
              <th style={th}>Δ vs champion</th>
              <th style={th}>Verdict</th>
            </tr>
          </thead>
          <tbody>
            {data.runs.map(r => (
              <tr key={r.id} style={{ borderBottom: '1px solid #f0f2f7', background: r.id === data.champion_run_id ? '#fffbe9' : 'transparent' }}>
                <td style={td}>
                  <Link to={`/runs/${r.id}`} style={{ color: '#2563eb', textDecoration: 'none' }}>{r.name}</Link>
                  {r.id === data.champion_run_id && ' 🏆'}
                </td>
                <td style={td}>{r.primary_value?.toFixed(4) ?? '—'}</td>
                <td style={{ ...td, color: r.delta_vs_champion_pct > 0 ? '#0b6b2f' : r.delta_vs_champion_pct < 0 ? '#a02121' : '#5b6472' }}>
                  {r.delta_vs_champion_pct === null ? '—' : `${r.delta_vs_champion_pct > 0 ? '+' : ''}${r.delta_vs_champion_pct}%`}
                </td>
                <td style={td}><VerdictChip verdict={r.verdict.verdict} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="Parameter differences">
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ textAlign: 'left', color: '#5b6472', borderBottom: '1px solid #e4e9f2' }}>
              <th style={th}>param</th>
              {data.runs.map(r => <th key={r.id} style={th}>{r.name}</th>)}
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.param_diff).map(([k, info]) => (
              <tr key={k} style={{ borderBottom: '1px solid #f0f2f7', background: info.differs ? '#fdf3ff' : 'transparent' }}>
                <td style={{ ...td, fontWeight: 600 }}>{k}{info.differs && <span style={{ color: '#9333ea', marginLeft: 4 }}>•</span>}</td>
                {info.values.map((v, i) => (
                  <td key={i} style={td}>{v === undefined ? '—' : String(v)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title={`${metric} curves`}>
        <MetricChart
          series={data.runs.map((r, i) => ({
            label: r.name,
            points: runs[r.id]?.metrics?.[metric] || [],
          }))}
        />
      </Card>
    </div>
  );
}

const th = { padding: '8px 10px', fontWeight: 600, fontSize: 12 };
const td = { padding: '9px 10px' };
