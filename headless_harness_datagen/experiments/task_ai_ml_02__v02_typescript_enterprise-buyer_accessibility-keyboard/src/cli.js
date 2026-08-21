#!/usr/bin/env node
const { loadExperiments, saveExperiments } = require('./persistence');
function generateId(){return Date.now().toString(36)+Math.random().toString(36).substr(2,5);}


function printHelp() {
  console.log('Usage: cli <command> [options]');
  console.log('Commands:');
  console.log('  create <name> [description]   Create a new experiment');
  console.log('  list                           List all experiments');
  console.log('  get <id>                       Show details of an experiment');
}

function create(name, description) {
  if (!name) {
    console.error('Error: name is required');
    process.exit(1);
  }
  const experiments = loadExperiments();
  const newExp = {
    id: uuidv4(),
    name,
    description: description || '',
    createdAt: new Date().toISOString(),
    status: 'running',
  };
  experiments.push(newExp);
  saveExperiments(experiments);
  console.log('Created experiment:', newExp.id);
}

function list() {
  const experiments = loadExperiments();
  if (experiments.length === 0) {
    console.log('No experiments found.');
    return;
  }
  experiments.forEach((exp) => {
    console.log(`${exp.id}\t${exp.name}\t${exp.status}\t${exp.createdAt}`);
  });
}

function get(id) {
  const experiments = loadExperiments();
  const exp = experiments.find((e) => e.id === id);
  if (!exp) {
    console.error('Experiment not found');
    process.exit(1);
  }
  console.log(JSON.stringify(exp, null, 2));
}

function main() {
  const args = process.argv.slice(2);
  const cmd = args[0];
  switch (cmd) {
    case 'create':
      create(args[1], args[2]);
      break;
    case 'list':
      list();
      break;
    case 'get':
      get(args[1]);
      break;
    default:
      printHelp();
      process.exit(0);
  }
}

main();
