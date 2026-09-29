# Start ERP services via Docker Compose and verify backend readiness.
param(
    [int]$WaitSeconds = 60
)

function Get-DockerComposeCommand {
    if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        return 'docker-compose'
    }
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        return 'docker compose'
    }
    throw 'Docker Compose not found. Install Docker Desktop or Docker engine with Compose support.'
}

$composeCommand = Get-DockerComposeCommand
Write-Host "Starting ERP services via Docker Compose..."
& $composeCommand up --build -d

Write-Host "Waiting for backend to respond on http://127.0.0.1:8000/docs"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$healthScript = Join-Path $scriptDir 'ci_healthcheck.ps1'
if (-not (Test-Path $healthScript)) {
    Write-Error "Health check script not found: $healthScript"
    exit 1
}

& $healthScript -wait $WaitSeconds

Write-Host "ERP services started. Open http://127.0.0.1:8000/docs in your browser."
