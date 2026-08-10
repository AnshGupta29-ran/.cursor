import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home.jsx';
import Experiments from './pages/Experiments.jsx';
import RunDetail from './pages/RunDetail.jsx';

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/experiments" element={<Experiments />} />
        <Route path="/run/:runId" element={<RunDetail />} />
      </Routes>
    </Router>
  );
}
