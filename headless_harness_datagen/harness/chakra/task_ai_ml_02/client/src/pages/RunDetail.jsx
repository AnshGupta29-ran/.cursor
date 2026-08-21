import React, { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api.js';
import { Card, Loading, ErrorBox, Empty, VerdictChip, MetricChart, btn } from '../components.jsx';

export default function RunDetail() {
  const { id } = useParams();
  const [run, setRun] = useState(null);
  const [verdict, setVerdict] = useState(null);
  const [arts, setArts] = useState([]);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState(null);
  const [uploadErr, setUploadErr] = useState(null);
  const fileRef = useRef();

  const load = async () => {
    try {
      const r = await api.getRun(id);
      setRun(r);
      if (r.status !== 'RUNNING') {
        try { setVerdict(await api.getVerdict(id)); } catch {}
      }
      setArts(await api.listArtifacts(id));
    } catch (e) { setError(e); }
  };
  useEffect(() => { load(); }, [id]);

  if (error) return <ErrorBox error={error} />;
  if (!run) return <Loading />;

  const metricKeys = Object.keys(run.metrics || {});

  const upload = async (ev) => {
    const f = ev.target.files[0];
    if (!f) return;
    setUploadErr(null);
    try {
      const buf = await f.arrayBuffer();
      await api.uploadArtifact(id, f.name, f.type || 'text/plain', buf);
      setArts(await api.listArtifacts(id));
    } catch (e) { setUploadErr(e); }
    ev.target.value = '';
  };

  const showPreview = async (aid) => {
    try { setPreview(await api.previewArtifact(aid)); } catch (e) { setPreview({ name: '?', preview: `Preview unavailable: ${e.message}` }); }
  };

  return (
    <div>
      <Link to={`/experiments/${run.experiment_id}`} style={{ color: '#2563eb', textDecoration: 'none', fontSize: 13 }}>← experiment</Link>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 4 }}>
        <h2 style={{ margin: 0 }}>{run.name}</h2>
        <span style={{ fontSize: 12, color: '#7c8698' }}>{run.status}</span>
      </div>

      {verdict && (
        <div style={{
          margin: '14px 0', padding: 16, borderRadius: 10,
          background: verdict.verdict === 'PASS' ? '#eefbf2' : verdict.verdict === 'REGRESSED' ? '#fdf0ef' : '#f4f6fa',
          border: `1px solid ${verdict.verdict === 'PASS' ? '#b9e8c8' : verdict.verdict === 'REGRESSED' ? '#f2c6c3' : '#e4e9f2'}`,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
            <VerdictChip verdict={verdict.verdict} />
            <strong style={{ fontSize: 15 }}>Promotion gate verdict</strong>
          </div>
          <p style={{ margin: 0, fontSize: 14, color: '#39465c' }}>{verdict.summary}</p>
        </div>
      )}

      <Card title="Parameters">
        {Object.keys(run.params || {}).length === 0 ? <Empty>No params logged</Empty> : (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {Object.entries(run.params).map(([k, v]) => (
              <span key={k} style={{ background: '#eef1f6', borderRadius: 6, padding: '4px 10px', fontSize: 13 }}>
                <strong>{k}</strong> = {String(v)}
              </span>
            ))}
          </div>
        )}
      </Card>

      {metricKeys.map(mk => (
        <Card key={mk} title={`Metric: ${mk}`}>
          <MetricChart
            series={[{ label: run.name, points: run.metrics[mk] }]}
            notes={run.curve_notes?.[mk] || []}
          />
        </Card>
      ))}

      <Card
        title={`Artifacts (${arts.length})`}
        actions={
          <>
            <input ref={fileRef} type="file" style={{ display: 'none' }} onChange={upload} />
            <button style={btn.primary} onClick={() => fileRef.current.click()}>Upload artifact</button>
          </>
        }
      >
        {uploadErr && <ErrorBox error={uploadErr} />}
        {arts.length === 0 ? <Empty>No artifacts yet — upload a classification report, JSON metrics dump, or CSV.</Empty> : (
          <ul style={{ margin: 0, paddingLeft: 0, listStyle: 'none' }}>
            {arts.map(a => (
              <li key={a.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: '1px solid #f0f2f7', fontSize: 14 }}>
                <span style={{ fontWeight: 600 }}>{a.name}</span>
                <span style={{ color: '#7c8698', fontSize: 12 }}>{a.content_type} · {(a.size / 1024).toFixed(1)} KB</span>
                <span style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
                  <button style={btn.ghost} onClick={() => showPreview(a.id)}>Preview</button>
                  <a href={`/api/artifacts/${a.id}`} style={{ ...btn.ghost, textDecoration: 'none', display: 'inline-block' }}>Download</a>
                </span>
              </li>
            ))}
          </ul>
        )}
        {preview && (
          <div style={{ marginTop: 12, background: '#10192b', color: '#d4e2f7', borderRadius: 8, padding: 14 }}>
            <div style={{ fontSize: 12, color: '#8fa3bf', marginBottom: 6 }}>Preview: {preview.name}</div>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: 12, maxHeight: 300, overflow: 'auto' }}>{preview.preview}</pre>
          </div>
        )}
      </Card>
    </div>
  );
}
