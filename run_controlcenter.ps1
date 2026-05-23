$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

Write-Host "========================================" -ForegroundColor DarkGray
Write-Host "Controlcenter launcher" -ForegroundColor Cyan
Write-Host "Starting Vite site from .\Controlcenter" -ForegroundColor DarkYellow
Write-Host "========================================" -ForegroundColor DarkGray

$packageJson = Join-Path $PSScriptRoot "Controlcenter\package.json"
if (-not (Test-Path $packageJson)) {
    Write-Host "[ERROR] Controlcenter package.json not found:" -ForegroundColor Red
    Write-Host "        Controlcenter\package.json" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] npm was not found in PATH." -ForegroundColor Red
    Write-Host "Install Node.js 20+ and reopen this terminal." -ForegroundColor Yellow
    exit 1
}

Set-Location -Path (Join-Path $PSScriptRoot "Controlcenter")

if (-not (Test-Path "node_modules")) {
    Write-Host "[INFO] node_modules not found. Installing Controlcenter dependencies..." -ForegroundColor Yellow
    & npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] npm install failed." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Write-Host "[INFO] Running Controlcenter build..." -ForegroundColor Cyan
& npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] npm run build failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "[INFO] Controlcenter is starting. Vite will print the actual local URL below." -ForegroundColor Green
Write-Host "       Preferred URL: http://127.0.0.1:4173/" -ForegroundColor Green
Write-Host ""

& npm run dev -- --host 127.0.0.1 --port 4173
exit $LASTEXITCODE
