$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
 docker info --format '{{.ServerVersion}}'
 if ($LASTEXITCODE -ne 0) { throw 'Open Docker Desktop and wait until its Linux engine is running, then retry.' }
 docker compose up --build -d
 if ($LASTEXITCODE -ne 0) { throw 'Compose startup failed' }
 $ready = $false
 for ($attempt = 0; $attempt -lt 40; $attempt++) {
  try { Invoke-RestMethod 'http://127.0.0.1:8082/api/health' | Out-Null; $ready = $true; break } catch { Start-Sleep 2 }
 }
 if (!$ready) { throw 'Agent did not become ready; inspect docker compose logs' }
 python scripts/check-workspace.py --url http://127.0.0.1:8082 --output workspace-postgres.json
 if ($LASTEXITCODE -ne 0) { throw 'Authenticated workspace verification failed' }
 python scripts/check-lifecycle.py --url http://127.0.0.1:8082
 if ($LASTEXITCODE -ne 0) { throw 'Document lifecycle verification failed' }
 python scripts/benchmark.py --url http://127.0.0.1:8082 --rounds 20 --output benchmark-postgres.json
 if ($LASTEXITCODE -ne 0) { throw 'Scenario benchmark failed' }
 docker compose exec -T postgres psql -U agentshield -d agentshield -c 'SELECT decision, analyzer_mode, COUNT(*) FROM audit_decisions GROUP BY decision, analyzer_mode;'
 if ($LASTEXITCODE -ne 0) { throw 'SQL reporting check failed' }
 Write-Host 'PostgreSQL-backed scenario sweep complete. Dashboard: http://127.0.0.1:3000'
} finally { Pop-Location }
