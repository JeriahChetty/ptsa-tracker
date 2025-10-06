# Test the container locally before deploying to Azure

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

Write-Log "Testing PTSA Tracker container locally..." "Green"
Write-Log "=========================================" "Green"

# Stop any existing test containers
Write-Log "Cleaning up existing test containers..." "Yellow"
docker stop ptsa-tracker-local-test 2>$null
docker rm ptsa-tracker-local-test 2>$null

# Run the container locally
Write-Log "Starting container locally..." "Yellow"
$testContainer = docker run -d --name ptsa-tracker-local-test -p 5002:5000 `
    -e FLASK_ENV=production `
    -e DATABASE_URL="sqlite:////app/instance/ptsa.db" `
    -e HOST=0.0.0.0 `
    -e PORT=5000 `
    ptsa-tracker:latest

if ($LASTEXITCODE -ne 0) {
    Write-Log "Failed to start container" "Red"
    exit 1
}

Write-Log "Container started with ID: $testContainer" "Green"
Write-Log "Waiting 30 seconds for startup..." "Yellow"
Start-Sleep -Seconds 30

# Get container logs
Write-Log "Container logs:" "Yellow"
$logs = docker logs ptsa-tracker-local-test 2>&1
Write-Log $logs "White"

# Test the application
Write-Log "Testing application..." "Yellow"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5002" -TimeoutSec 15 -UseBasicParsing
    Write-Log "✅ SUCCESS! Local test passed" "Green"
    Write-Log "Status Code: $($response.StatusCode)" "Green"
    Write-Log "Your container is ready for Azure deployment!" "Green"
} catch {
    Write-Log "❌ Local test failed: $($_.Exception.Message)" "Red"
    Write-Log "Check the logs above for issues" "Yellow"
}

# Clean up
Write-Log "Cleaning up test container..." "Yellow"
docker stop ptsa-tracker-local-test
docker rm ptsa-tracker-local-test

Write-Log "Local test completed!" "Green"
