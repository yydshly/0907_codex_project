$ErrorActionPreference = 'Stop'
$a2fPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $a2fPython)) { throw '请先根据 README 安装独立运行环境。' }
& $a2fPython (Join-Path $PSScriptRoot 'scripts/serve.py') --port 8015
