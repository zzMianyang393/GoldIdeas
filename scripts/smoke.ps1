$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $root ".venv\Scripts\python.exe"

if (!(Test-Path $venvPython)) {
  & (Join-Path $PSScriptRoot "check.cmd")
}

& $venvPython (Join-Path $PSScriptRoot "smoke_flow.py")
