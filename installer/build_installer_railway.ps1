$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

$venvPython = ".\.venv\Scripts\python.exe"
$venvPyinstaller = ".\.venv\Scripts\pyinstaller.exe"
$issScript = ".\installer\bjjvienna_railway.iss"

if (-not (Test-Path $venvPython)) {
    Write-Error "Missing .venv Python at $venvPython. Create venv and install requirements first."
}

if (-not (Test-Path $venvPyinstaller)) {
    Write-Error "Missing PyInstaller at $venvPyinstaller. Install requirements into .venv first."
}

Write-Host "[1/3] Building executable with PyInstaller..."
& $venvPyinstaller --noconfirm --clean gui.spec

if (-not (Test-Path ".\dist\gui.exe")) {
    Write-Error "Build failed: dist\gui.exe was not generated."
}

Write-Host "[2/3] Looking for Inno Setup compiler (ISCC)..."
$iscc = Get-Command iscc -ErrorAction SilentlyContinue
if (-not $iscc) {
    $candidate = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
    if (Test-Path $candidate) {
        $iscc = $candidate
    }
}

if (-not $iscc) {
    Write-Warning "Inno Setup (ISCC) not found. Installer .exe was not generated."
    Write-Host "Portable binary available at dist\gui.exe"
    exit 0
}

Write-Host "[3/3] Building installer with Inno Setup..."
if ($iscc -is [string]) {
    $isccExe = $iscc
} else {
    $isccExe = $iscc.Source
}
& $isccExe $issScript

if (Test-Path ".\dist\BJJVienna-Setup-Railway.exe") {
    Write-Host "Done: dist\BJJVienna-Setup-Railway.exe"
} else {
    Write-Warning "ISCC finished, but dist\BJJVienna-Setup-Railway.exe was not found."
}
