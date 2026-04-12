@echo off
echo Starting MSME Finance Platform...
echo.

echo Starting services in separate windows...

REM Start Celery Worker
start "Celery Worker" cmd /k "cd C:\MsmeFundingPlatform\oracle && venv\Scripts\activate && celery -A tasks.celery_app worker --loglevel=info --pool=solo"

REM Wait 5 seconds
timeout /t 5

REM Start FastAPI Server
start "FastAPI Server" cmd /k "cd C:\MsmeFundingPlatform\oracle && venv\Scripts\activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo ✅ Services starting in separate windows
echo.
echo API will be available at: http://localhost:8000/docs
echo.
pause