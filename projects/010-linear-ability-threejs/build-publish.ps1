$ErrorActionPreference = 'Stop'
$workspaceRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$sourceRoot = Join-Path $workspaceRoot 'upstream/linear-ability-threejs'
$publishRoot = Join-Path $workspaceRoot 'docs/demos/010-linear-ability-threejs'
& (Join-Path $PSScriptRoot 'start.ps1')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'demo/vite.publish.config.js') -Destination $sourceRoot -Force
Push-Location $sourceRoot
try {
  node node_modules/vite/bin/vite.js build --config vite.publish.config.js
  if ($LASTEXITCODE -ne 0) { throw 'Static build failed' }
} finally { Pop-Location }
New-Item -ItemType Directory -Path (Join-Path $publishRoot 'assets') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $sourceRoot 'dist-publish/showcase.html') -Destination (Join-Path $publishRoot 'index.html') -Force
Get-ChildItem -LiteralPath (Join-Path $sourceRoot 'dist-publish/assets') -File | ForEach-Object {
  Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $publishRoot 'assets') -Force
}
Copy-Item -LiteralPath (Join-Path $sourceRoot 'node_modules/three/LICENSE') -Destination (Join-Path $publishRoot 'THREE-LICENSE.txt') -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'demo/THIRD_PARTY_NOTICES.md') -Destination $publishRoot -Force
Write-Host "Static files ready: $publishRoot"
