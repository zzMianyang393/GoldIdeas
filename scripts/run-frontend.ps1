$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Push-Location (Join-Path $root "web")
npm run dev -- --host 127.0.0.1 --port 5180
Pop-Location
