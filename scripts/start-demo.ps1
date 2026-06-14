$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$mutex = [System.Threading.Mutex]::new(
    $false,
    "Global\IntelligentSlackKnowledgeBaseDemo"
)
$mutexAcquired = $false

function Invoke-Migrations {
    $migrationProcess = Start-Process `
        -FilePath "$projectRoot\.venv\Scripts\slack-kb-migrate.exe" `
        -WorkingDirectory $projectRoot `
        -WindowStyle Hidden `
        -Wait `
        -PassThru
    return $migrationProcess.ExitCode
}

try {
    $mutexAcquired = $mutex.WaitOne(0)
    if (-not $mutexAcquired) {
        Write-Host "The demo stack is already running."
        return
    }

    $staleRuntimeProcesses = Get-CimInstance Win32_Process | Where-Object {
        $_.ProcessId -ne $PID -and (
            (
                $_.ExecutablePath -like "$projectRoot\*" -and
                $_.CommandLine -match "slack-kb\.exe|uvicorn slack_kb\.api"
            ) -or (
                $_.Name -eq "uv.exe" -and
                $_.CommandLine -match "\brun slack-kb\b"
            )
        )
    }
    foreach ($process in $staleRuntimeProcesses) {
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
    }

    Write-Host "Checking local Supabase..."
    $statusProcess = Start-Process `
        -FilePath "npx.cmd" `
        -ArgumentList "--yes", "supabase@latest", "status" `
        -WorkingDirectory $projectRoot `
        -WindowStyle Hidden `
        -Wait `
        -PassThru
    if ($statusProcess.ExitCode -ne 0) {
        npx.cmd --yes supabase@latest start
    }

    Write-Host "Applying database migrations..."
    if ((Invoke-Migrations) -ne 0) {
        Write-Host "Database was not ready. Restarting local Supabase once..."
        npx.cmd --yes supabase@latest stop
        if ($LASTEXITCODE -ne 0) {
            throw "Could not stop local Supabase."
        }
        npx.cmd --yes supabase@latest start
        if ($LASTEXITCODE -ne 0) {
            throw "Could not start local Supabase."
        }
        if ((Invoke-Migrations) -ne 0) {
            throw "Database migrations failed after restarting local Supabase."
        }
    }
    Write-Host "Database migrations applied."

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
} finally {
    if ($mutexAcquired) {
        $mutex.ReleaseMutex()
    }
    $mutex.Dispose()
}
