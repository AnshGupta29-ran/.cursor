@echo off
REM EpochLedger one-command dev startup for Windows: uvicorn :8000 + Vite :5173
cd /d %~dp0

echo Starting EpochLedger API on http://127.0.0.1:8000 ...
start "epochledger-api" cmd /c "python -m uvicorn app:app --host 127.0.0.1 --port 8000"

echo Starting EpochLedger SPA on http://127.0.0.1:5173 ...
cd client
start "epochledger-web" cmd /c "npm run dev"

echo.
echo   SPA:  http://127.0.0.1:5173
echo   API:  http://127.0.0.1:8000/api/health
echo.
