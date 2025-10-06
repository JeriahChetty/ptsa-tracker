# Install Docker Compose on Windows
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Create the directory for Docker Compose
$composeDir = "$Env:ProgramFiles\Docker\cli-plugins"
if (-not (Test-Path $composeDir)) {
    New-Item -ItemType Directory -Path $composeDir -Force
}

# Download Docker Compose
$composeUrl = "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-windows-x86_64.exe"
$composePath = "$composeDir\docker-compose.exe"
Invoke-WebRequest -Uri $composeUrl -OutFile $composePath

# Verify installation
docker compose version

Write-Host "Docker Compose installed successfully. You can now use 'docker compose' commands."
