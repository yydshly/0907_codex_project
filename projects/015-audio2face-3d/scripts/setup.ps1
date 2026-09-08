$ErrorActionPreference = 'Stop'
$a2fRoot = Split-Path $PSScriptRoot -Parent
Push-Location $a2fRoot
try {
    New-Item -ItemType Directory -Force vendor | Out-Null
    $env:GIT_LFS_SKIP_SMUDGE = '1'
    $a2fRepos = @{
        'Audio2Face-3D' = '4d61b6b81ad7b5108512ea0eab10d8712ea4a236'
        'Audio2Face-3D-SDK' = '1ca0f02535ed774f5dbcd724a31cd486368dc783'
        'Audio2Face-3D-training-framework' = '112c5eb3408afd065ac8974b2c6ea9ab0e3965c6'
        'Maya-ACE' = 'f0dc13670952c495450dab1655c94e9056c9d7d9'
    }
    foreach ($a2fRepo in $a2fRepos.Keys) {
        $a2fCheckout = Join-Path 'vendor' $a2fRepo
        if (-not (Test-Path -LiteralPath $a2fCheckout)) {
            git clone --no-checkout "https://github.com/NVIDIA/$a2fRepo.git" $a2fCheckout
            if ($LASTEXITCODE -ne 0) { throw "下载失败：$a2fRepo" }
            git -C $a2fCheckout checkout $a2fRepos[$a2fRepo]
            if ($LASTEXITCODE -ne 0) { throw "版本检出失败：$a2fRepo" }
        }
    }
    git -C vendor/Maya-ACE lfs pull --include='sample_project/maya_geom/mark_geom_v2_topo1.ma'
    if ($LASTEXITCODE -ne 0) { throw '人物资源下载失败' }
    if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) { python -m venv .venv }
    & .venv/Scripts/python.exe -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw '依赖安装失败' }
    & .venv/Scripts/python.exe scripts/download_model.py
    if ($LASTEXITCODE -ne 0) { throw '模型下载失败' }
    & .venv/Scripts/python.exe scripts/extract_geometry.py
    if ($LASTEXITCODE -ne 0) { throw '网格提取失败' }
    Write-Host '环境已准备。运行 start.ps1，然后打开 http://127.0.0.1:8015'
} finally { Pop-Location }
