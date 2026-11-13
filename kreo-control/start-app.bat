@echo off
title Kreo Control Desktop Launcher
echo ========================================================
echo    Starting Kreo Control Desktop Application...
echo ========================================================
echo.

cd /d "%~dp0"

echo [*] Launching FastAPI Backend on port 8000...
start "Kreo Control Backend (Port 8000)" cmd /k "cd /d %~dp0backend && uv run uvicorn kreo_control.api.app:app --port 8000"

echo [*] Launching Vite Frontend on port 5173...
start "Kreo Control Frontend (Port 5173)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo [*] Waiting for services to initialize...
timeout /t 4 /nobreak >nul

echo [*] Opening application in browser...
start http://localhost:5173

echo.
echo ========================================================
echo [+] Kreo Control is now running!
echo     Backend API:  http://127.0.0.1:8000
echo     Frontend UI:  http://localhost:5173
echo ========================================================
echo.
echo Keep the backend and frontend terminal windows open while using Kreo Control.
pause
