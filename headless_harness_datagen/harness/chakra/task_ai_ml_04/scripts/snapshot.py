import argparse
import hashlib
import os
from pathlib import Path
from flask import Flask
import csv
import json
import sys

# Import the app
import importlib.util

APP_PATH = Path(__file__).parent.parent / 'app.py'
spec = importlib.util.spec_from_file_location('app', APP_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
app = mod.app

# Ensure data dir exists
DATA_DIR = Path(__file__).parent.parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

def clear_csvs():
    for name in ['documents.csv','chunks.csv','queries.csv','answers.csv','request_log.csv']:
        p = DATA_DIR / name
        if p.exists():
            p.unlink()

def ingest_fixture(client, fixture_path):
    with open(fixture_path, 'rb') as f:
        data = {'file': (os.path.basename(fixture_path), f, 'text/plain')}
        resp = client.post('/upload', data=data, content_type='multipart/form-data')
        assert resp.status_code == 200, f'Upload failed: {resp.status_code}'

def ask_question(client, question):
    resp = client.post('/ask', data={'question': question})
    assert resp.status_code == 200, f'Ask failed: {resp.status_code}'
    return resp.get_data(as_text=True)

def run_snapshot(seed:int):
    # deterministic seed usage not needed currently, but we include for compliance
    import random
    random.seed(seed)
    clear_csvs()
    client = app.test_client()
    # Ingest sample fixture
    fixture = Path(__file__).parent.parent / 'fixtures' / 'sample.txt'
    ingest_fixture(client, fixture)
    # Ask a couple of questions
    answers = []
    for q in ["What was discussed?", "What was the vote outcome?"]:
        answers.append(ask_question(client, q))
    # Build simple HTML report
    html = "<html><head><title>Snapshot</title></head><body>"
    html += f"<h1>Snapshot seed {seed}</h1>"
    for i, ans in enumerate(answers):
        html += f"<h2>Q{i+1}: {['What was discussed?','What was the vote outcome?'][i]}</h2>"
        html += ans
    html += "</body></html>"
    out_dir = Path(__file__).parent.parent.parent / 'snapshots'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'run_{seed}.html'
    out_path.write_text(html, encoding='utf-8')
    print(f'Wrote snapshot to {out_path}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    run_snapshot(args.seed)
