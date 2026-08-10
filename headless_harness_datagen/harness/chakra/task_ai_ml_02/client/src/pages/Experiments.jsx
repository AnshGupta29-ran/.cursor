import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listExperiments } from '../api';

export default function Experiments() {
  const [experiments, setExperiments] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    listExperiments()
      .then(setExperiments)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div>Error: {error}</div>;
  return (
    <div style={{ padding: '2rem' }}>
      <h1>Experiments</h1>
      <ul>
        {experiments.map((exp) => (
          <li key={exp.id}>
            <strong>{exp.name}</strong> (ID: {exp.id})
            <br />
            <Link to={`/run/${exp.champion_run_id}`}>View Champion Run</Link>
          </li>
        ))}
      </ul>
      <Link to="/">← Home</Link>
    </div>
  );
}
