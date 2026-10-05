param([switch]$Codex)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Run install.ps1 first' }
if ($Codex) {
    codex mcp add mustang-tone -- $taskPython -m mustang.cli mcp
    if ($LASTEXITCODE -ne 0) { throw 'Codex MCP registration failed' }
    $taskSkill = Join-Path $env:USERPROFILE '.codex\skills\mustang-tone'
    New-Item -ItemType Directory -Path $taskSkill -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $taskRoot 'skills\mustang-tone\SKILL.md') -Destination (Join-Path $taskSkill 'SKILL.md')
} else {
    @{mcpServers=@{'mustang-tone'=@{command=$taskPython;args=@('-m','mustang.cli','mcp')}}} |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskRoot 'local-config.json') -Encoding utf8
    Write-Host 'Generated local-config.json. Import this configuration in your MCP client.'
}
