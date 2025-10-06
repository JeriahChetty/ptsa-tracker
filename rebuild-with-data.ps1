# Rebuild container with local database included

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    # Handle emoji and special characters that cause encoding issues
    $CleanMessage = $Message -replace '[^\x00-\x7F]', '?' # Replace non-ASCII with ?
    
    try {
        # Validate color parameter
        $ValidColors = @("Black", "DarkBlue", "DarkGreen", "DarkCyan", "DarkRed", "DarkMagenta", "DarkYellow", "Gray", "DarkGray", "Blue", "Green", "Cyan", "Red", "Magenta", "Yellow", "White")
        if ($ValidColors -contains $Color) {
            Write-Host "[$ts] $CleanMessage" -ForegroundColor $Color
        } else {
            Write-Host "[$ts] $CleanMessage"
        }
    } catch {
        # Fallback if color still fails
        Write-Host "[$ts] $CleanMessage"
    }
}

Write-Log "Rebuild Container with Local Database" "Green"
Write-Log "=========================================" "Green"

# Step 1: Copy local database to be included in Docker build
Write-Log "Preparing local database for container build..." "Yellow"

if (Test-Path "instance\ptsa_dev.db") {
    # Create instance directory if it doesn't exist
    if (-not (Test-Path "instance")) {
        New-Item -ItemType Directory -Path "instance" -Force
    }
    
    # Copy the dev database as the production database
    Copy-Item "instance\ptsa_dev.db" "instance\ptsa.db" -Force
    Write-Log "Database prepared for container build" "Green"
} else {
    Write-Log "Local database not found. Run comprehensive_seed.py first." "Red"
    exit 1
}

# Step 2: Rebuild the Docker image
Write-Log "Building Docker image with local data..." "Yellow"
docker build -t ptsa-tracker:latest .

if ($LASTEXITCODE -eq 0) {
    Write-Log "Docker image built successfully" "Green"
} else {
    Write-Log "Docker build failed" "Red"
    exit 1
}

# Step 3: Push to Azure Container Registry
Write-Log "Pushing to Azure Container Registry..." "Yellow"
az acr login --name acrptsa298
docker tag ptsa-tracker:latest acrptsa298.azurecr.io/ptsa-tracker:latest
docker push acrptsa298.azurecr.io/ptsa-tracker:latest

Write-Log "Image pushed to registry" "Green"

# Step 4: Deploy the updated container
Write-Log "Deploying updated container..." "Yellow"
.\cleanup-and-deploy.ps1

Write-Log "Deployment with local data completed!" "Green"
Write-Log "Your PTSA Tracker with all local data should now be available online!" "Cyan"
