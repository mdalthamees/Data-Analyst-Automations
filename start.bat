@echo off
echo ========================================================
echo    DataPilot AI - Autonomous Data Analyst Platform
echo ========================================================
echo.

if not exist "venv" (
    echo [1/3] Creating Python Virtual Environment...
    python -m venv venv
    call .\venv\Scripts\activate
    pip install -r backend\requirements.txt
) else (
    echo [1/3] Activating Virtual Environment...
    call .\venv\Scripts\activate
)

echo [2/3] Checking Node modules...
if not exist "frontend\node_modules" (
    cd frontend
    call npm install
    call npm run build
    cd ..
)

echo [3/3] Launching DataPilot AI Server...
echo Application URL: http://127.0.0.1:8000
echo.
cd backend
..\venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
