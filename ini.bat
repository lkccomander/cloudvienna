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
python gui.py
