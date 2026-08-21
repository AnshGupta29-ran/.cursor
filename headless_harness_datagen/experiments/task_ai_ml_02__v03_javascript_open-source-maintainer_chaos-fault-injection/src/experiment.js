// experiment.js – core logic for managing experiment runs
import { randomUUID } from 'crypto'; // use built‑in crypto for UUID strings
import { initCsv, appendLine, readAll, CSV_PATH } from './persistence.js';
import { maybeInject } from './chaos.js';

/** Ensure the CSV is ready */
export function ensureInitialized() {
  try {
    const fs = require('fs');
    if (!fs.existsSync(CSV_PATH)) {
      initCsv();
    }
  } catch (e) {
    initCsv();
  }
}

/** Start a new experiment run */
export function startRun(name) {
  const runId = randomUUID();
  const line = `${runId},${name},RUNNING,, ,${Date.now()}`;
  const maybe = maybeInject(line);
  appendLine(maybe);
  return runId;
}

/** Log a metric for a run */
export function logMetric(runId, metricName, metricValue) {
  const line = `${runId},,RUNNING,${metricName},${metricValue},${Date.now()}`;
  const maybe = maybeInject(line);
  appendLine(maybe);
}

/** Finish a run */
export function finishRun(runId) {
  const line = `${runId},,FINISHED,, ,${Date.now()}`;
  const maybe = maybeInject(line);
  appendLine(maybe);
}

/** Get all rows (raw objects) */
export function getAllRuns() {
  return readAll();
}
