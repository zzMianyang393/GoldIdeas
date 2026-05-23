$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $root ".venv\Scripts\python.exe"

if (!(Test-Path $venvPython)) {
  & (Join-Path $PSScriptRoot "check.cmd")
}

Push-Location (Join-Path $root "web")
npm ci
npm run build
Pop-Location

& $venvPython (Join-Path $PSScriptRoot "package_release.py")
