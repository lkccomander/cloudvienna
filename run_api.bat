@echo off
setlocal

REM Always run from this script's folder.
cd /d "%~dp0"

if not exist ".venv\Scripts\activate" (
    echo [ERROR] Virtual environment activation script not found:
    echo         .venv\Scripts\activate.bat
    echo Create it first with: py -m venv .venv
    exit /b 1
)

call ".venv\Scripts\activate"

REM Auto-install dependencies only if key API packages are missing.
python -c "import fastapi,uvicorn,dotenv" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Missing dependencies detected. Installing from requirements.txt...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed.
        exit /b 1
    )
)

python -m backend.run
