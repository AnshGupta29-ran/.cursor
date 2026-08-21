const fs = require('fs');
const path = require('path');

const DATA_FILE = path.resolve(__dirname, '..', 'data', 'experiments.json');

function ensureDataDir() {
  const dir = path.dirname(DATA_FILE);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

/** Load experiments from JSON file */
function loadExperiments() {
  ensureDataDir();
  if (!fs.existsSync(DATA_FILE)) {
    return [];
  }
  const raw = fs.readFileSync(DATA_FILE, { encoding: 'utf-8' });
  try {
    return JSON.parse(raw);
  } catch (e) {
    return [];
  }
}

/** Save experiments array to JSON file */
function saveExperiments(exps) {
  ensureDataDir();
  const data = JSON.stringify(exps, null, 2);
  fs.writeFileSync(DATA_FILE, data, { encoding: 'utf-8' });
}

module.exports = { loadExperiments, saveExperiments, DATA_FILE };
