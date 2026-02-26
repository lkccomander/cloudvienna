@echo off
setlocal

REM Always run from this script's folder.
cd /d "%~dp0"

set "APP_ENV=cloud"

REM Startup banner
powershell -NoProfile -Command "Write-Host '========================================' -ForegroundColor DarkGray; Write-Host 'Cloud launcher (APP_ENV fixed to cloud)' -ForegroundColor Cyan; Write-Host ('Using APP_ENV=' + $env:APP_ENV) -ForegroundColor DarkYellow; Write-Host '========================================' -ForegroundColor DarkGray"

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

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment activation script not found:
    echo         .venv\Scripts\activate.bat
    echo Create it first with: py -m venv .venv
    exit /b 1
)

call ".venv\Scripts\activate.bat"

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

REM Strict config validation + bootstrap fallback.
python scripts\check_instance_config.py --env %APP_ENV%
if errorlevel 1 (
    echo [INFO] Missing or invalid config detected. Running bootstrap for APP_ENV=%APP_ENV%...
    python scripts\bootstrap_instance.py --env %APP_ENV%
    if errorlevel 1 (
        echo [ERROR] Bootstrap failed. API will not start.
        exit /b 1
    )
    python scripts\check_instance_config.py --env %APP_ENV%
    if errorlevel 1 (
        echo [ERROR] Configuration is still invalid after bootstrap.
        exit /b 1
    )
)

python -m backend.run
