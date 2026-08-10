import React from 'react';
import { Link } from 'react-router-dom';
import { seedDemo } from '../api';

export default function Home() {
  const handleSeed = async () => {
    try {
      const data = await seedDemo();
      alert('Demo seeded. Experiment ID: ' + data.experiment_id);
    } catch (e) {
      alert('Error seeding demo: ' + e.message);
    }
  };
  return (
    <div style={{ padding: '2rem' }}>
      <h1>EpochLedger Demo</h1>
      <p>Welcome to the demo application.</p>
      <button onClick={handleSeed}>Seed Demo Data</button>
      <br />
      <Link to="/experiments">View Experiments</Link>
    </div>
  );
}
