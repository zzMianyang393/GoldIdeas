$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$webDir = Join-Path $root "web"
$distIndex = Join-Path $webDir "dist\index.html"

if (!(Test-Path $distIndex)) {
  Push-Location $webDir
  npm run build
  Pop-Location
}

$html = Get-Content $distIndex -Raw
if ($html -notmatch '<div id="root">') {
  throw "Built frontend HTML root was not found."
}
if ($html -notmatch '/assets/') {
  throw "Built frontend assets were not referenced."
}

$assets = Get-ChildItem (Join-Path $webDir "dist\assets") -ErrorAction SilentlyContinue
if (!$assets) {
  throw "Built frontend assets directory is empty."
}

Write-Host "Frontend smoke passed."
