# show_python_versions.ps1
Write-Host "=== Python del sistema ==="
python --version
if ($LASTEXITCODE -ne 0) { py -V }

Write-Host "`n=== Python en .venv (si existe) ==="
if (Test-Path ".\.venv\Scripts\python.exe") {
    .\.venv\Scripts\python.exe --version
} else {
    Write-Host ".venv no encontrado"
}

Write-Host "`n=== Python en .venv-linux (si existe) ==="
if (Test-Path ".\.venv-linux\bin\python") {
    .\.venv-linux\bin\python --version
} else {
    Write-Host ".venv-linux no encontrado (normal en Windows)"
}
