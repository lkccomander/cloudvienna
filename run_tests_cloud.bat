@echo off
setlocal

REM Always run from this script's folder.
cd /d "%~dp0"

set "APP_ENV=cloud"

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
python -m pytest -q
