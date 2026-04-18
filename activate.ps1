<#
.SYNOPSIS
Activate this project's Windows Python virtual environment.

.DESCRIPTION
Run from PowerShell:
  .\activate.ps1

If script execution is blocked, allow local scripts for your user:
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#>

$ErrorActionPreference = "Stop"

$ProjectRoot = if ($PSScriptRoot) {
    $PSScriptRoot
} else {
    Split-Path -Parent $MyInvocation.MyCommand.Path
}

Set-Location $ProjectRoot
$env:APP_ENV = "cloud"

Write-Host "========================================" -ForegroundColor DarkGray
Write-Host "Cloud launcher (APP_ENV fixed to cloud)" -ForegroundColor Cyan
Write-Host "Using APP_ENV=$env:APP_ENV" -ForegroundColor DarkYellow
Write-Host "========================================" -ForegroundColor DarkGray

$venvDir = Join-Path $ProjectRoot ".venv"
$pyvenvCfg = Join-Path $venvDir "pyvenv.cfg"
$activateScript = Join-Path $venvDir "Scripts\Activate.ps1"

if (Test-Path $pyvenvCfg) {
    $isLinuxVenv = Select-String -Path $pyvenvCfg -Pattern "^home = /usr/bin" -Quiet
    if ($isLinuxVenv) {
        Write-Host "[ERROR] The current .venv was created in WSL/Linux and cannot run in Windows." -ForegroundColor Red
        Write-Host "Recreate the virtual environment from PowerShell:"
        Write-Host "  rmdir /s /q .venv"
        Write-Host "  py -m venv .venv"
        Write-Host "  .\.venv\Scripts\Activate.ps1"
        Write-Host "  python -m pip install -r requirements.txt"
        exit 1
    }
}

if (-not (Test-Path $activateScript)) {
    Write-Host "[ERROR] Virtual environment activation script not found:" -ForegroundColor Red
    Write-Host "        .venv\Scripts\Activate.ps1"
    Write-Host "Create it first with: py -m venv .venv"
    exit 1
}

. $activateScript
