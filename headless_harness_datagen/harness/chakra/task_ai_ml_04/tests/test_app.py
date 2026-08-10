import os
import hashlib
import pytest
from pathlib import Path

# Import the Flask app
import importlib.util

APP_PATH = Path(__file__).parent.parent / 'app.py'
spec = importlib.util.spec_from_file_location('app', APP_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
app = mod.app

@pytest.fixture
def client():
    # Ensure fresh data directory for each test run
    data_dir = Path(__file__).parent.parent / 'data'
    # Remove existing CSV files if any
    for f in data_dir.glob('*.csv'):
        f.unlink()
    # Recreate CSV headers by importing the module (which runs init_csv)
    import importlib
    importlib.reload(mod)
    with app.test_client() as client:
        yield client

def test_upload_success(client):
    txt_path = Path(__file__).parent.parent / 'fixtures' / 'sample.txt'
    with open(txt_path, 'rb') as f:
        data = {'file': (os.path.basename(txt_path), f, 'text/plain')}
        resp = client.post('/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    # Verify documents.csv has one entry
    docs = (Path(__file__).parent.parent / 'data' / 'documents.csv').read_text()
    assert len(docs.strip().split('\n')) == 2  # header + row

def test_duplicate_upload(client):
    txt_path = Path(__file__).parent.parent / 'fixtures' / 'sample.txt'
    with open(txt_path, 'rb') as f:
        data = {'file': (os.path.basename(txt_path), f, 'text/plain')}
        client.post('/upload', data=data, content_type='multipart/form-data')
    # Second upload should be 409
    with open(txt_path, 'rb') as f:
        data = {'file': (os.path.basename(txt_path), f, 'text/plain')}
        resp = client.post('/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 409

def test_ask_returns_citation(client):
    # Upload first
    txt_path = Path(__file__).parent.parent / 'fixtures' / 'sample.txt'
    with open(txt_path, 'rb') as f:
        data = {'file': (os.path.basename(txt_path), f, 'text/plain')}
        client.post('/upload', data=data, content_type='multipart/form-data')
    # Ask a question that should match the text
    resp = client.post('/ask', data={'question': 'What was discussed?'})
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    # Stub banner should be present and a citation link
    assert 'Stub LLM' in html
    assert '/chunk/' in html

def test_chunk_view(client):
    txt_path = Path(__file__).parent.parent / 'fixtures' / 'sample.txt'
    with open(txt_path, 'rb') as f:
        data = {'file': (os.path.basename(txt_path), f, 'text/plain')}
        client.post('/upload', data=data, content_type='multipart/form-data')
    # Retrieve a chunk id from chunks.csv
    chunks_file = Path(__file__).parent.parent / 'data' / 'chunks.csv'
    lines = chunks_file.read_text().splitlines()
    assert len(lines) > 1
    chunk_id = lines[1].split(',')[0]
    resp = client.get(f'/chunk/{chunk_id}')
    assert resp.status_code == 200
    assert chunk_id in resp.get_data(as_text=True)

def test_history_persistence(client):
    txt_path = Path(__file__).parent.parent / 'fixtures' / 'sample.txt'
    with open(txt_path, 'rb') as f:
        data = {'file': (os.path.basename(txt_path), f, 'text/plain')}
        client.post('/upload', data=data, content_type='multipart/form-data')
    client.post('/ask', data={'question': 'vote outcome'})
    # Access history page
    resp = client.get('/history')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'vote outcome' in html
