$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$systemPython = "C:\Program Files\Python312\python.exe"

function Resolve-Python {
  if (Test-Path $venvPython) {
    return $venvPython
  }
  if (Test-Path $systemPython) {
    return $systemPython
  }
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    return $python.Source
  }
  throw "Python 3 was not found. Install Python 3.12 or update scripts\check.ps1."
}

$python = Resolve-Python

if (!(Test-Path $venvPython)) {
  Write-Host "Creating local virtual environment..."
  & $python -m venv (Join-Path $root ".venv")
  $python = $venvPython
}

Write-Host "Installing backend dependencies..."
& $venvPython -m pip install --no-cache-dir -r (Join-Path $root "server\requirements.txt")

Write-Host "Compiling backend Python modules..."
& $venvPython -m py_compile `
  (Join-Path $root "server\demand_pipeline.py") `
  (Join-Path $root "server\app.py") `
  (Join-Path $root "server\storage.py") `
  (Join-Path $root "server\ai_reports.py") `
  (Join-Path $root "server\ai_jobs.py") `
  (Join-Path $root "server\ai_providers.py")

Write-Host "Running backend tests..."
& $venvPython (Join-Path $root "server\test_pipeline.py")

Write-Host "Running HTTP smoke flow..."
& $venvPython (Join-Path $root "scripts\smoke_flow.py")

Write-Host "Building frontend..."
Push-Location (Join-Path $root "web")
npm run build
Pop-Location

Write-Host "Running frontend smoke flow..."
& (Join-Path $root "scripts\frontend-smoke.cmd")

Write-Host "GoldIdeas check completed successfully."
