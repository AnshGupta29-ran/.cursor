#!/usr/bin/env bash
set -e

# Ensure required commands are available
command -v uvicorn >/dev/null 2>&1 || { echo "uvicorn not found - install with 'pip install uvicorn'"; exit 1; }

# Start FastAPI server in background
uvicorn src.epochledger.main:app --host 127.0.0.1 --port 8000 &
FASTAPI_PID=$!

# Wait for health endpoint to become ready
until curl -s http://127.0.0.1:8000/api/health >/dev/null; do
  sleep 0.2
done

echo "FastAPI server is up. PID=$FASTAPI_PID"

echo "Press Ctrl+C to stop."

# Forward signals to child process
trap "kill $FASTAPI_PID" SIGINT SIGTERM EXIT

wait $FASTAPI_PID
