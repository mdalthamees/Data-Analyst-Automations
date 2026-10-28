@echo off
echo Starting DataPilot AI Backend (FastAPI + DuckDB)...
call .\venv\Scripts\activate
cd backend
..\venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
