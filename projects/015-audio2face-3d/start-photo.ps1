$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path -LiteralPath '.cache/photo-runtime-ready.json')) {
    throw '请先运行 python scripts/setup_photo.py，安装照片口播模型与独立环境。'
}
& '.cache/sadtalker-venv/Scripts/python.exe' 'scripts/serve_photo.py'
