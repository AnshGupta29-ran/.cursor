import React, { useEffect, useState } from 'react';
import { api } from '../api.js';
import { Card, Loading, ErrorBox, Empty, btn } from '../components.jsx';

export default function Activity() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);

  const load = () => api.getActivity().then(r => setRows([...r].reverse())).catch(setError);
  useEffect(() => { load(); const t = setInterval(load, 3000); return () => clearInterval(t); }, []);

  if (error) return <ErrorBox error={error} />;
  if (!rows) return <Loading />;

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>API activity — last {rows.length} calls</h2>
      <Card actions={<button style={btn.ghost} onClick={load}>Refresh</button>}>
        {rows.length === 0 ? <Empty>No API calls yet.</Empty> : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ textAlign: 'left', color: '#5b6472', borderBottom: '1px solid #e4e9f2' }}>
                <th style={th}>Time</th>
                <th style={th}>Method</th>
                <th style={th}>Path</th>
                <th style={th}>Status</th>
                <th style={th}>Latency</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #f0f2f7' }}>
                  <td style={td}>{new Date(r.timestamp * 1000).toLocaleTimeString()}</td>
                  <td style={td}><code>{r.method}</code></td>
                  <td style={{ ...td, fontFamily: 'monospace', fontSize: 12 }}>{r.path}</td>
                  <td style={{ ...td, color: r.status < 400 ? '#0b6b2f' : '#a02121', fontWeight: 700 }}>{r.status}</td>
                  <td style={td}>{r.latency_ms} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}

const th = { padding: '8px 10px', fontWeight: 600, fontSize: 12 };
const td = { padding: '8px 10px' };
