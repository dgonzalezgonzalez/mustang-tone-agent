$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $taskRoot
$taskPython = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
if (-not (Test-Path -LiteralPath '.venv-audio\Scripts\python.exe')) {
    if (Test-Path -LiteralPath $taskPython) { & $taskPython -m venv .venv-audio }
    else { py -3.12 -m venv .venv-audio }
}
$taskWorker = Join-Path $taskRoot '.venv-audio\Scripts\python.exe'
& $taskWorker -m pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) { throw 'CPU PyTorch installation failed' }
& $taskWorker -m pip install -r requirements-separator-lock.txt --no-deps
if ($LASTEXITCODE -ne 0) { throw 'Separator installation failed' }
Write-Host 'Separator installed. The first separation downloads the htdemucs_6s weights.'
