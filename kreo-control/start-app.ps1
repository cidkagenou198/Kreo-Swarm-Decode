# Kreo Control Desktop Launcher
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   Starting Kreo Control Desktop Application..." -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Start Backend in separate window
Write-Host "[*] Starting FastAPI Backend on port 8000..." -ForegroundColor Yellow
$BackendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$Root\backend'; Write-Host '--- Kreo Control Backend (FastAPI on Port 8000) ---' -ForegroundColor Magenta; uv run uvicorn kreo_control.api.app:app --port 8000" -PassThru

# 2. Start Frontend in separate window
Write-Host "[*] Starting Vite Frontend on port 5173..." -ForegroundColor Yellow
$FrontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$Root\frontend'; Write-Host '--- Kreo Control Frontend (Vite on Port 5173) ---' -ForegroundColor Magenta; npm run dev" -PassThru

Start-Sleep -Seconds 3

# 3. Open Browser
Write-Host "[*] Launching Kreo Control in default browser..." -ForegroundColor Green
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "[+] Kreo Control is up and running!" -ForegroundColor Green
Write-Host "    Backend API: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "    Frontend UI: http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "Leave this window open. Type 'q' and press Enter only when you want to exit and shut down all servers." -ForegroundColor Yellow

while ($true) {
    $input = Read-Host
    if ($input -eq "q" -or $input -eq "quit" -or $input -eq "exit") {
        break
    }
}

Write-Host "[*] Stopping services..." -ForegroundColor Yellow
Stop-Process -Id $BackendProcess.Id -ErrorAction SilentlyContinue
Stop-Process -Id $FrontendProcess.Id -ErrorAction SilentlyContinue
Write-Host "[+] Services stopped cleanly." -ForegroundColor Green
