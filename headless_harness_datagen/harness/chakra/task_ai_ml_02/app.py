import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any
import uuid
import time

from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory stores
experiments: Dict[str, Dict] = {}
runs: Dict[str, Dict] = {}

class ExperimentCreate(BaseModel):
    name: str
    gate_policy: Dict[str, Any] = {}

class RunLog(BaseModel):
    experiment_id: str
    name: str
    params: Dict[str, Any] = {}
    metrics: Dict[str, List[Dict[str, Any]]] = {}

@app.post('/api/experiment')
def create_experiment(payload: ExperimentCreate):
    exp_id = str(uuid.uuid4())
    experiments[exp_id] = {
        'id': exp_id,
        'name': payload.name,
        'gate_policy': payload.gate_policy,
        'champion_run_id': None,
        'runs': [],
        'created_at': time.time()
    }
    return {'id': exp_id}

@app.get('/api/experiment')
def list_experiments():
    return list(experiments.values())

@app.post('/api/run')
def create_run(payload: RunLog):
    if payload.experiment_id not in experiments:
        raise HTTPException(status_code=404, detail='Experiment not found')
    run_id = str(uuid.uuid4())
    run = {
        'id': run_id,
        'experiment_id': payload.experiment_id,
        'name': payload.name,
        'params': payload.params,
        'metrics': payload.metrics,
        'status': 'FINISHED',
        'started_at': time.time(),
        'finished_at': time.time()
    }
    runs[run_id] = run
    experiments[payload.experiment_id]['runs'].append(run_id)
    return {'id': run_id}

@app.get('/api/run/{run_id}')
def get_run(run_id: str):
    if run_id not in runs:
        raise HTTPException(status_code=404, detail='Run not found')
    return runs[run_id]

@app.post('/api/demo/seed')
def seed_demo():
    # deterministic seed data
    exp_id = str(uuid.uuid4())
    experiments[exp_id] = {
        'id': exp_id,
        'name': 'sentiment-sweep',
        'gate_policy': {'primary_metric': 'accuracy', 'min_delta_pct': 1.0},
        'champion_run_id': None,
        'runs': [],
        'created_at': time.time()
    }
    # create 8 runs
    for i in range(1, 9):
        run_id = str(uuid.uuid4())
        run = {
            'id': run_id,
            'experiment_id': exp_id,
            'name': f'run-{i}',
            'params': {'learning_rate': 0.01 * i, 'batch_size': 32},
            'metrics': {'accuracy': [{'step': s, 'value': 0.7 + 0.03 * i} for s in range(5)]},
            'status': 'FINISHED',
            'started_at': time.time(),
            'finished_at': time.time()
        }
        runs[run_id] = run
        experiments[exp_id]['runs'].append(run_id)
    # set champion (best accuracy)
    champion = max(experiments[exp_id]['runs'], key=lambda rid: runs[rid]['metrics']['accuracy'][-1]['value'])
    experiments[exp_id]['champion_run_id'] = champion
    return {'experiment_id': exp_id, 'champion_run_id': champion}

@app.get('/api/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
