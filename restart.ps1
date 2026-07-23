# InstaGuard Launcher & Restart Script
# ─────────────────────────────────────────────────────────────────
# Automatically detects Docker. If Docker is installed, runs containers.
# If Docker is not installed, runs FastAPI and React locally with SQLite.
# ─────────────────────────────────────────────────────────────────

Set-Location "$PSScriptRoot"

$dockerAvailable = (Get-Command docker -ErrorAction SilentlyContinue) -or (Get-Command docker-compose -ErrorAction SilentlyContinue)

if ($dockerAvailable) {
    Write-Host "InstaGuard: Restarting Docker containers..." -ForegroundColor Cyan
    docker-compose down
    docker-compose up --build -d
    Write-Host ""
    Write-Host "Done! InstaGuard running at http://localhost:3000" -ForegroundColor Green
} else {
    Write-Host "Docker not detected. Starting InstaGuard in Local mode (FastAPI + Vite)..." -ForegroundColor Cyan

    if (-not (Test-Path "backend\.venv")) {
        Write-Host "Creating Python virtual environment in backend\.venv..." -ForegroundColor Yellow
        python -m venv backend\.venv
        & "backend\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
    }

    if (-not (Test-Path "frontend\node_modules")) {
        Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
        Set-Location "$PSScriptRoot\frontend"
        npm install
        Set-Location "$PSScriptRoot"
    }

    Write-Host "Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Yellow
    $backend = Start-Process -FilePath "$PSScriptRoot\backend\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn app:app --host 0.0.0.0 --port 8000" -WorkingDirectory "$PSScriptRoot\backend" -PassThru

    Write-Host "Starting React Frontend on http://localhost:3000 ..." -ForegroundColor Yellow
    $frontend = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev" -WorkingDirectory "$PSScriptRoot\frontend" -PassThru

    Write-Host ""
    Write-Host "InstaGuard running successfully!" -ForegroundColor Green
    Write-Host "Frontend: http://localhost:3000" -ForegroundColor Green
    Write-Host "Backend API: http://localhost:8000" -ForegroundColor Green
}
