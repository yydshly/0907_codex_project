$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$workerPython = [IO.Path]::GetFullPath((Join-Path $projectRoot '.cache/sadtalker-venv/Scripts/python.exe'))
if (!(Test-Path -LiteralPath $workerPython)) { throw 'Model runtime missing; prepare the local models first.' }
$servicePython = (& $workerPython -c 'import sys; print(sys._base_executable)').Trim()
$existingWorker = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -like '*performance_worker.py*' -and $_.ExecutablePath -eq $workerPython }
if (!$existingWorker) {
    Start-Process -FilePath $workerPython -ArgumentList 'scripts/performance_worker.py' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput "$projectRoot/.cache/performance-worker.log" -RedirectStandardError "$projectRoot/.cache/performance-worker-error.log"
}
$listener = Get-NetTCPConnection -State Listen -LocalPort 8022 -ErrorAction SilentlyContinue
if (!$listener) {
    Start-Process -FilePath $servicePython -ArgumentList 'scripts/serve_performance.py' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput "$projectRoot/.cache/performance-server.log" -RedirectStandardError "$projectRoot/.cache/performance-server-error.log"
}
Write-Output 'Workbench: http://127.0.0.1:8022/ (model warmup runs in the background)'
