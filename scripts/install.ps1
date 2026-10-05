param([switch]$SkipWinget)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $taskRoot
if (-not $SkipWinget) {
    foreach ($taskPackage in @('Python.Python.3.12','Google.PlatformTools','Gyan.FFmpeg','OpenJS.NodeJS.LTS')) {
        winget install --id $taskPackage --exact --silent --accept-source-agreements --accept-package-agreements
    }
}
$taskPython = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
if ((Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    # Reuse an existing environment.
} elseif (-not (Test-Path -LiteralPath $taskPython)) {
    py -3.12 -m venv .venv
} elseif (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    & $taskPython -m venv .venv
}
$taskVenv = Join-Path $taskRoot '.venv\Scripts\python.exe'
& $taskVenv -c "import sys; assert sys.version_info[:2] == (3, 12), 'Python 3.12 is required'"
if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 is required. Install Python 3.12 and retry.' }
& $taskVenv -m pip install -r requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& $taskVenv -m pip install -e . --no-deps
if ($LASTEXITCODE -ne 0) { throw 'Application installation failed' }
Push-Location web
try {
    npm ci --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw 'UI dependencies failed' }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw 'UI build failed' }
} finally { Pop-Location }
Write-Host 'Installed. Run scripts\start.ps1. Connect the amp USB and unlocked Android phone.'
$taskShell = New-Object -ComObject WScript.Shell
$taskShortcut = $taskShell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Mustang Tone Agent.lnk'))
$taskShortcut.TargetPath = Join-Path $taskRoot 'Start Mustang Tone Agent.cmd'
$taskShortcut.WorkingDirectory = $taskRoot
$taskShortcut.Save()
