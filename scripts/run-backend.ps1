$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$systemPython = "C:\Program Files\Python312\python.exe"

if (!(Test-Path $venvPython)) {
  if (!(Test-Path $systemPython)) {
    throw "Python 3.12 was not found. Run scripts\check.ps1 after installing Python 3."
  }
  & $systemPython -m venv (Join-Path $root ".venv")
}

& $venvPython -m pip install --no-cache-dir -r (Join-Path $root "server\requirements.txt")
& $venvPython (Join-Path $root "server\app.py")
