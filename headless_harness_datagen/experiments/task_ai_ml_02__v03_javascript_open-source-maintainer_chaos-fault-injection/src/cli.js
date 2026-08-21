// cli.js – tiny command‑line interface for the experiment journal

import { ensureInitialized, startRun, logMetric, finishRun, getAllRuns } from './experiment.js';
import { initCsv, readAll } from './persistence.js';

// Simple async wrapper (not really async now) for top‑level await compatibility
(async () => {
  const args = process.argv.slice(2);
  const cmd = args[0];

  switch (cmd) {
    case 'init':
      initCsv();
      console.log('✅ CSV initialised at', require('./persistence.js').CSV_PATH);
      break;
    case 'start': {
      const name = args[1] || 'unnamed';
      ensureInitialized();
      const runId = startRun(name);
      console.log('🚀 Started run', runId);
      break;
    }
    case 'log': {
      const [runId, metricName, metricValue] = args.slice(1);
      if (!runId || !metricName || metricValue === undefined) {
        console.error('Usage: log <runId> <metricName> <metricValue>');
        process.exit(1);
      }
      ensureInitialized();
      logMetric(runId, metricName, metricValue);
      console.log(`📈 Logged ${metricName}=${metricValue} for ${runId}`);
      break;
    }
    case 'finish': {
      const runId = args[1];
      if (!runId) {
        console.error('Usage: finish <runId>');
        process.exit(1);
      }
      ensureInitialized();
      finishRun(runId);
      console.log('🏁 Finished run', runId);
      break;
    }
    case 'list': {
      const rows = getAllRuns();
      console.table(rows);
      break;
    }
    default:
      console.error('Unknown command. Available: init, start <name>, log <runId> <metric> <value>, finish <runId>, list');
      process.exit(1);
  }
})();
