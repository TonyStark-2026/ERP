# Stop ERP services and remove volumes via Docker Compose.
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
Write-Host "Stopping ERP services..."
& $composeCommand down --volumes --remove-orphans
Write-Host "ERP services stopped and cleaned up."
