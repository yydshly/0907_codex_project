$ErrorActionPreference = 'Stop'
$workspaceRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$sourceRoot = Join-Path $workspaceRoot 'upstream/linear-ability-threejs'
if (!(Test-Path -LiteralPath (Join-Path $sourceRoot 'package.json'))) {
  git clone https://github.com/achrefelouafi/LinearAbilityExtThreeJS.git $sourceRoot
  if ($LASTEXITCODE -ne 0) { throw 'Clone failed' }
  git -C $sourceRoot checkout bf58757ab9b6057515470aa074cdb4026bc54ed7
  if ($LASTEXITCODE -ne 0) { throw 'Checkout failed' }
}
if (!(Test-Path -LiteralPath (Join-Path $sourceRoot 'node_modules/vite/bin/vite.js'))) {
  Push-Location $sourceRoot
  try { npm.cmd ci --no-audit --no-fund; if ($LASTEXITCODE -ne 0) { throw 'Install failed' } } finally { Pop-Location }
}
foreach ($demoFile in @('showcase.html', 'skills.html', 'lab.js', 'lab.css', 'vite.showcase.config.js')) {
  Copy-Item -LiteralPath (Join-Path $PSScriptRoot "demo/$demoFile") -Destination (Join-Path $sourceRoot $demoFile) -Force
}
# Remove only the generated first-version entry, which would shadow the new Vite page.
$legacyEntry = Join-Path $sourceRoot 'public/showcase.html'
if (Test-Path -LiteralPath $legacyEntry) { Remove-Item -LiteralPath $legacyEntry }
if (!(Get-NetTCPConnection -LocalPort 5190 -State Listen -ErrorAction SilentlyContinue)) {
  $nodePath = (Get-Command node.exe).Source
  Start-Process -FilePath $nodePath -ArgumentList 'node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','5190','--strictPort' -WorkingDirectory $sourceRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot 'vite.log') -RedirectStandardError (Join-Path $PSScriptRoot 'vite-error.log') | Out-Null
} else { Write-Host 'Port 5190 already has a listener; existing service was preserved.' }
Write-Host 'Showcase: http://127.0.0.1:5190/showcase.html'
Write-Host 'Original: http://127.0.0.1:5190/'
