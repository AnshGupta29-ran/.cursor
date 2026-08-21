import { Experiment } from './experiment';
import * as fs from 'fs';
import * as path from 'path';

const DATA_FILE = path.resolve(__dirname, '..', 'data', 'experiments.json');

/** Ensure the data directory exists */
function ensureDataDir() {
  const dir = path.dirname(DATA_FILE);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

/** Load experiments from the JSON file. Returns empty array if file missing. */
export function loadExperiments(): Experiment[] {
  ensureDataDir();
  if (!fs.existsSync(DATA_FILE)) {
    return [];
  }
  const raw = fs.readFileSync(DATA_FILE, { encoding: 'utf-8' });
  try {
    return JSON.parse(raw) as Experiment[];
  } catch {
    return [];
  }
}

/** Persist the given array of experiments to disk. */
export function saveExperiments(exps: Experiment[]): void {
  ensureDataDir();
  const data = JSON.stringify(exps, null, 2);
  fs.writeFileSync(DATA_FILE, data, { encoding: 'utf-8' });
}
