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
New-Item -ItemType Directory -Path $publishRoot -Force | Out-Null
$builtRoot = Join-Path $sourceRoot 'dist-publish'
Copy-Item -LiteralPath (Join-Path $builtRoot 'showcase.html') -Destination (Join-Path $publishRoot 'index.html') -Force
Copy-Item -LiteralPath (Join-Path $builtRoot 'index.html') -Destination (Join-Path $publishRoot 'original.html') -Force
Copy-Item -LiteralPath (Join-Path $builtRoot 'skills.html') -Destination $publishRoot -Force
foreach ($folder in @('assets', 'models', 'hdri', 'textures')) {
  Copy-Item -LiteralPath (Join-Path $builtRoot $folder) -Destination $publishRoot -Recurse -Force
}
# Only prune obsolete generated bundles, never source files or public models.
$assetRoot = Join-Path $publishRoot 'assets'
Get-ChildItem -LiteralPath $assetRoot -File | Where-Object {
  !(Test-Path -LiteralPath (Join-Path $builtRoot ('assets/' + $_.Name)))
} | ForEach-Object { Remove-Item -LiteralPath $_.FullName }
Copy-Item -LiteralPath (Join-Path $sourceRoot 'node_modules/three/LICENSE') -Destination (Join-Path $publishRoot 'THREE-LICENSE.txt') -Force
Copy-Item -LiteralPath (Join-Path $sourceRoot 'LICENSE') -Destination (Join-Path $publishRoot 'UPSTREAM-LICENSE.txt') -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'demo/THIRD_PARTY_NOTICES.md') -Destination $publishRoot -Force
Write-Host "Static files ready: $publishRoot"
