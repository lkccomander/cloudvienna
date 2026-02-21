@echo off
setlocal

REM Always run from this script's folder.
cd /d "%~dp0"

if exist ".venv\pyvenv.cfg" (
    findstr /b /c:"home = /usr/bin" ".venv\pyvenv.cfg" >nul
    if not errorlevel 1 (
        echo [ERROR] The current .venv was created in WSL/Linux and cannot run in Windows.
        echo Recreate the virtual environment from PowerShell:
        echo   rmdir /s /q .venv
        echo   py -m venv .venv
        echo   .venv\Scripts\activate
        echo   python -m pip install -r requirements.txt
        exit /b 1
    )
)

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
