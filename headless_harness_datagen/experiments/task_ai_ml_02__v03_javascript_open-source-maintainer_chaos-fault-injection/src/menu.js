// menu.js – tiny interactive TUI for EpochLedger

import * as readline from 'readline';
import { ensureInitialized, startRun, logMetric, finishRun, getAllRuns } from './experiment.js';
import { initCsv } from './persistence.js';

// Helper to ask a question and get a promise
function ask(query) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise(resolve => rl.question(query, ans => { rl.close(); resolve(ans); }));
}

async function main() {
  console.log('EpochLedger CLI');
  while (true) {
    console.log('\n1) Initialise CSV');
    console.log('2) List experiments');
    console.log('3) Add experiment');
    console.log('4) Delete experiment (not implemented)');
    console.log('5) Exit');
    const choice = await ask('Select option: ');
    switch (choice.trim()) {
      case '1':
        initCsv();
        console.log('✅ CSV initialised');
        break;
      case '2':
        console.table(getAllRuns());
        break;
      case '3': {
        const name = await ask('Experiment name: ');
        ensureInitialized();
        const runId = startRun(name || 'unnamed');
        const metric = await ask('Metric name (or empty to skip): ');
        if (metric) {
          const value = await ask('Metric value: ');
          logMetric(runId, metric, value);
        }
        finishRun(runId);
        console.log('✅ Experiment added and finished');
        break;
      }
      case '4':
        console.log('Delete not implemented in this demo');
        break;
      case '5':
        console.log('Bye!');
        process.exit(0);
      default:
        console.log('Invalid choice');
    }
  }
}

main();
