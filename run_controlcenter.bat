@echo off
setlocal

REM Always run from this script's folder.
cd /d "%~dp0"

REM Startup banner
powershell -NoProfile -Command "Write-Host '========================================' -ForegroundColor DarkGray; Write-Host 'Controlcenter launcher' -ForegroundColor Cyan; Write-Host 'Starting Vite site from .\Controlcenter' -ForegroundColor DarkYellow; Write-Host '========================================' -ForegroundColor DarkGray"

if not exist "Controlcenter\package.json" (
    echo [ERROR] Controlcenter package.json not found:
    echo         Controlcenter\package.json
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm was not found in PATH.
    echo Install Node.js 20+ and reopen this terminal.
    exit /b 1
)

cd /d "%~dp0Controlcenter"

if not exist "node_modules" (
    echo [INFO] node_modules not found. Installing Controlcenter dependencies...
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed.
        exit /b 1
    )
)

echo [INFO] Controlcenter will be available at:
echo        http://127.0.0.1:4173/
echo.

call npm run dev -- --host 127.0.0.1 --port 4173
