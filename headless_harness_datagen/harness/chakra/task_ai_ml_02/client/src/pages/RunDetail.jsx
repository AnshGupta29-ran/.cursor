import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getRun } from '../api';

export default function RunDetail() {
  const { runId } = useParams();
  const [run, setRun] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (runId) {
      getRun(runId)
        .then(setRun)
        .catch((e) => setError(e.message));
    }
  }, [runId]);

  if (error) return <div>Error: {error}</div>;
  if (!run) return <div>Loading...</div>;

  return (
    <div style={{ padding: '2rem' }}>
      <h2>Run Detail</h2>
      <p><strong>ID:</strong> {run.id}</p>
      <p><strong>Name:</strong> {run.name}</p>
      <p><strong>Status:</strong> {run.status}</p>
      <pre>{JSON.stringify(run, null, 2)}</pre>
      <Link to="/experiments">← Back to Experiments</Link>
    </div>
  );
}
