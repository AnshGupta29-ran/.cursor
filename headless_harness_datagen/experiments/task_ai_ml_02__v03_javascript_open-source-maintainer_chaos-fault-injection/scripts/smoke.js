// scripts/smoke.js – basic smoke test for EpochLedger

import { ensureInitialized, startRun, logMetric, finishRun, getAllRuns } from '../src/experiment.js';

// Run the demo flow programmatically
function runSmoke() {
  // Ensure CSV exists
  ensureInitialized();

  // Start a run
  const runId = startRun('smoke_test');
  // Log a dummy metric
  logMetric(runId, 'dummy_metric', '123');
  // Finish the run
  finishRun(runId);

  // Retrieve all rows
  const rows = getAllRuns();
  if (!Array.isArray(rows) || rows.length === 0) {
    console.error('Smoke failed: no rows returned');
    process.exit(1);
  }
  // Simple sanity check: at least one FINISHED entry
  const hasFinished = rows.some(r => r.run_id === runId && r.status === 'FINISHED');
  if (!hasFinished) {
    console.error('Smoke failed: finished run not recorded');
    process.exit(1);
  }
  console.log('✅ Smoke test passed');
  process.exit(0);
}

runSmoke();
