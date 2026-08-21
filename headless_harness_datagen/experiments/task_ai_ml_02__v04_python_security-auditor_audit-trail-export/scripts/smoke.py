"""Smoke test for EpochLedger security auditor audit‑trail export demo.

It starts the FastAPI server in a subprocess, submits a test audit event via the
CLI helper, fetches the CSV export and performs a minimal validation (header
present and the test title appears). The server process is terminated before
exiting. The script exits with status code 0 on success, non‑zero otherwise.
"""

import subprocess
import sys
import time
import requests
import json
import os

SERVER_MODULE = "epochledger.server"
SERVER_URL = "http://127.0.0.1:8000"
TEST_TITLE = "Test login"
TEST_USER = "alice"
TEST_DESC = "Successful login"


def start_server():
    # Launch the FastAPI server as a background process.
    proc = subprocess.Popen([sys.executable, "-m", SERVER_MODULE],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    # Wait until the health endpoint responds.
    for _ in range(20):
        try:
            requests.get(f"{SERVER_URL}/events", timeout=1)
            return proc
        except Exception:
            time.sleep(0.3)
    proc.terminate()
    raise RuntimeError("Server failed to start")


def submit_event():
    payload = {"title": TEST_TITLE, "user": TEST_USER, "description": TEST_DESC}
    resp = requests.post(f"{SERVER_URL}/events", json=payload)
    resp.raise_for_status()
    return resp.json()


def export_csv():
    resp = requests.get(f"{SERVER_URL}/export")
    resp.raise_for_status()
    return resp.text


def validate_csv(csv_text: str) -> bool:
    lines = csv_text.strip().splitlines()
    if not lines:
        return False
    header = lines[0].split(",")
    expected = ["timestamp", "title", "user", "description"]
    if header != expected:
        return False
    # Check that our test event appears in any row.
    for row in lines[1:]:
        if TEST_TITLE in row and TEST_USER in row and TEST_DESC in row:
            return True
    return False


def main():
    proc = None
    try:
        proc = start_server()
        submit_event()
        csv_text = export_csv()
        if not validate_csv(csv_text):
            sys.exit(1)
    finally:
        if proc:
            proc.terminate()
            proc.wait()

if __name__ == "__main__":
    main()
