// persistence.js – simple CSV read/write helpers
import * as fs from 'fs';
import * as path from 'path';

const DATA_DIR = path.resolve(process.cwd(), 'data');
export const CSV_PATH = path.join(DATA_DIR, 'experiments.csv');

/** Ensure the data directory exists */
export function ensureDataDir() {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }
}

/** Initialise the CSV file with a header */
export function initCsv() {
  ensureDataDir();
  const header = 'run_id,experiment_name,status,metric_name,metric_value,timestamp\n';
  fs.writeFileSync(CSV_PATH, header, { encoding: 'utf8' });
}

/** Append a raw CSV line (without newline) */
export function appendLine(line) {
  ensureDataDir();
  fs.appendFileSync(CSV_PATH, line + '\n', { encoding: 'utf8' });
}

/** Read all CSV rows as objects */
export function readAll() {
  if (!fs.existsSync(CSV_PATH)) return [];
  const raw = fs.readFileSync(CSV_PATH, { encoding: 'utf8' }).trim();
  if (!raw) return [];
  const rows = raw.split('\n');
  const header = rows.shift().split(',');
  return rows.map(r => {
    const cols = r.split(',');
    const obj = {};
    header.forEach((h, i) => (obj[h] = cols[i]));
    return obj;
  });
}
