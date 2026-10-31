$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$agentDir = Join-Path $projectRoot 'agent'
$gatewayDir = Join-Path $projectRoot 'gateway'
$dashboardDir = Join-Path $projectRoot 'dashboard'
$venvDir = Join-Path $projectRoot '.venv'
$pythonExe = Join-Path $venvDir 'Scripts\python.exe'
if (!(Test-Path $pythonExe)) { python -m venv $venvDir; if ($LASTEXITCODE -ne 0) { throw 'Could not create local Python environment' } }
& $pythonExe -m pip install -r (Join-Path $agentDir 'requirements.txt') --disable-pip-version-check
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed' }
foreach ($envName in @('.env.local', '.env')) {
$envPath = Join-Path $projectRoot $envName
if (Test-Path $envPath) {
 foreach ($line in Get-Content -LiteralPath $envPath) {
  if ($line -match '^\s*(ANALYZER_MODE|META_API_KEY|MODEL_API_KEY|META_MODEL|META_BASE_URL|META_MAX_COMPLETION_TOKENS|META_TIMEOUT_SECONDS|META_REASONING_EFFORT|DATABASE_URL|DATABASE_URL_UNPOOLED|COOKIE_SECURE)=(.*)$') {
   if ($null -eq [Environment]::GetEnvironmentVariable($Matches[1], 'Process')) {
    [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2].Trim().Trim('"').Trim("'"), 'Process')
   }
  }
 }
}
}
Push-Location $gatewayDir
try { go build -buildvcs=false -o gateway.exe .; if ($LASTEXITCODE -ne 0) { throw 'Go build failed' } } finally { Pop-Location }
if (!(Test-Path (Join-Path $dashboardDir 'node_modules'))) { Push-Location $dashboardDir; try { npm.cmd ci; if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' } } finally { Pop-Location } }
$processes = @()
try {
 $processes += Start-Process $pythonExe -ArgumentList 'app.py' -WorkingDirectory $agentDir -WindowStyle Hidden -PassThru
 $processes += Start-Process (Join-Path $gatewayDir 'gateway.exe') -WorkingDirectory $gatewayDir -WindowStyle Hidden -PassThru
 $processes += Start-Process 'cmd.exe' -ArgumentList '/c npm.cmd run dev' -WorkingDirectory $dashboardDir -WindowStyle Hidden -PassThru
 Write-Host 'AgentShield: http://127.0.0.1:5173 — Ctrl+C to stop. Uses SQLite unless DATABASE_URL is set. .env settings are loaded without printing secrets.'
 while ($true) { Start-Sleep 1 }
} finally { foreach ($process in $processes) { taskkill /PID $process.Id /T /F 2>$null | Out-Null } }
