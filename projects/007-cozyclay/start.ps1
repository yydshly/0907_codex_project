$ErrorActionPreference = 'Stop'
$researchRoot = $PSScriptRoot
$workspaceRoot = Split-Path (Split-Path $researchRoot -Parent) -Parent
$sourceRoot = Join-Path $workspaceRoot 'upstream/cozyclay'
if (!(Test-Path -LiteralPath (Join-Path $sourceRoot 'package.json'))) { throw 'Missing upstream/cozyclay. See README for checkout instructions.' }
$nodePath = (Get-Command node.exe).Source
if (!(Test-Path -LiteralPath (Join-Path $sourceRoot 'node_modules/vite/bin/vite.js'))) {
  Push-Location $sourceRoot
  try { npm.cmd ci --no-audit --no-fund; if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' } } finally { Pop-Location }
}
if (!(Get-NetTCPConnection -LocalPort 5180 -State Listen -ErrorAction SilentlyContinue)) {
  Start-Process -FilePath $nodePath -ArgumentList 'node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','5180','--strictPort' -WorkingDirectory $sourceRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $researchRoot 'vite.log') -RedirectStandardError (Join-Path $researchRoot 'vite-error.log') | Out-Null
} else { Write-Host 'Port 5180 already has a service; confirm it is CozyClay before using the Studio link.' }
if (!(Get-NetTCPConnection -LocalPort 5187 -State Listen -ErrorAction SilentlyContinue)) {
  Start-Process -FilePath $nodePath -ArgumentList 'serve-guide.mjs' -WorkingDirectory $researchRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $researchRoot 'guide.log') -RedirectStandardError (Join-Path $researchRoot 'guide-error.log') | Out-Null
}
Write-Host 'Guide: http://127.0.0.1:5187/demos/007-cozyclay/'
Write-Host 'Studio: http://127.0.0.1:5180/app/?motion=/demo/walk-then-stop.npz'
