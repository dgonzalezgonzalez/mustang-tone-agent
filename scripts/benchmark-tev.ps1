param([ValidateSet('tev1:0.8b', 'tev1:4b')][string]$Model = 'tev1:0.8b')
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $taskRoot
ollama pull $Model
if ($LASTEXITCODE -ne 0) { throw 'Ollama 0.35 or later is required' }
& '.\.venv\Scripts\python.exe' -m mustang.cli tev-benchmark --model $Model
