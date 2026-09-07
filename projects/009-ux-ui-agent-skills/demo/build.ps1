$ErrorActionPreference = 'Stop'
$demoSource = $PSScriptRoot
$workspaceRoot = [System.IO.Path]::GetFullPath((Join-Path $demoSource '../../..'))
$demoDestination = Join-Path $workspaceRoot 'docs/demos/009-ux-ui-agent-skills'
New-Item -ItemType Directory -Path $demoDestination -Force | Out-Null
foreach ($asset in @('index.html', 'styles.css', 'app.js', 'effects.html', 'effects.css', 'effects.js', 'standards.html', 'THIRD_PARTY_NOTICES.md', 'LUCIDE_LICENSE.txt')) {
    Copy-Item -LiteralPath (Join-Path $demoSource $asset) -Destination (Join-Path $demoDestination $asset) -Force
}
Copy-Item -LiteralPath (Join-Path $demoSource 'samples') -Destination $demoDestination -Recurse -Force
Copy-Item -LiteralPath (Join-Path $demoSource '../assets/ux-ui-constraints.svg') -Destination (Join-Path $demoDestination 'ux-ui-constraints.svg') -Force
Write-Output 'Web 导览已同步至 docs/demos/009-ux-ui-agent-skills/'
