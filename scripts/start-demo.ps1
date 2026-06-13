$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "Checking local Supabase..."
npx.cmd --yes supabase@latest status *> $null
if ($LASTEXITCODE -ne 0) {
    npx.cmd --yes supabase@latest start
}

Write-Host "Applying database migrations..."
uv run slack-kb-migrate

Write-Host "Starting FastAPI at http://127.0.0.1:8000 ..."
$api = Start-Process `
    -FilePath "$projectRoot\.venv\Scripts\python.exe" `
    -ArgumentList "-m", "uvicorn", "slack_kb.api:app", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory $projectRoot `
    -WindowStyle Hidden `
    -PassThru

try {
    for ($attempt = 0; $attempt -lt 20; $attempt += 1) {
        try {
            $ready = Invoke-RestMethod -Uri "http://127.0.0.1:8000/readyz" -TimeoutSec 2
            if ($ready.status -eq "ready") {
                break
            }
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }

    Write-Host "Starting Slack Socket Mode bot. Press Ctrl+C to stop."
    uv run slack-kb
} finally {
    if ($api -and -not $api.HasExited) {
        Stop-Process -Id $api.Id -Force
    }
}
