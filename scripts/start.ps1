$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Run scripts\install.ps1 first' }
$taskData = Join-Path $env:LOCALAPPDATA 'MustangToneAgent'
New-Item -ItemType Directory -Path $taskData -Force | Out-Null
$taskHealthy = $false
try { $taskHealthy = (Invoke-RestMethod 'http://127.0.0.1:8765/health' -TimeoutSec 2).ok } catch {}
if (-not $taskHealthy) {
    Start-Process -FilePath $taskPython -ArgumentList '-m','mustang.cli','serve' -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskData 'server.log') -RedirectStandardError (Join-Path $taskData 'server-error.log')
    for ($taskAttempt=0; $taskAttempt -lt 20; $taskAttempt++) {
        Start-Sleep -Milliseconds 500
        try { if ((Invoke-RestMethod 'http://127.0.0.1:8765/health' -TimeoutSec 2).ok) { $taskHealthy=$true; break } } catch {}
    }
}
if (-not $taskHealthy) { throw "App failed to start. Inspect $taskData\server-error.log" }
$taskToken = (Get-Content -LiteralPath (Join-Path $taskData 'access.token') -Raw).Trim()
Start-Process "http://127.0.0.1:8765/#token=$taskToken"
