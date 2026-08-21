#!/usr/bin/env bash
# EpochLedger one-command dev startup: uvicorn :8000 + Vite :5173 (proxy /api → :8000)
set -e
cd "$(dirname "$0")"

echo "Starting EpochLedger API on http://127.0.0.1:8000 ..."
python -m uvicorn app:app --host 127.0.0.1 --port 8000 &
API_PID=$!

echo "Starting EpochLedger SPA on http://127.0.0.1:5173 ..."
cd client
npm run dev &
WEB_PID=$!

trap "kill $API_PID $WEB_PID 2>/dev/null" EXIT

echo ""
echo "  SPA:  http://127.0.0.1:5173"
echo "  API:  http://127.0.0.1:8000/api/health"
echo ""
wait
