# Deploy PTSA Tracker with comprehensive seeded data

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $CleanMessage = $Message -replace '[^\x00-\x7F]', ''
    
    try {
        $ValidColors = @("Black", "DarkBlue", "DarkGreen", "DarkCyan", "DarkRed", "DarkMagenta", "DarkYellow", "Gray", "DarkGray", "Blue", "Green", "Cyan", "Red", "Magenta", "Yellow", "White")
        if ($ValidColors -contains $Color) {
            Write-Host "[$ts] $CleanMessage" -ForegroundColor $Color
        } else {
            Write-Host "[$ts] $CleanMessage"
        }
    } catch {
        Write-Host "[$ts] $CleanMessage"
    }
}

Write-Log "Deploy PTSA Tracker with Comprehensive Seeded Data" "Green"
Write-Log "==================================================" "Green"

# Step 1: Create comprehensive seeded database locally
Write-Log "Creating comprehensive seeded database..." "Yellow"

# Remove existing database first
if (Test-Path "instance\ptsa_dev.db") {
    Remove-Item "instance\ptsa_dev.db" -Force
    Write-Log "Removed existing database" "White"
}

if (Test-Path "instance\ptsa.db") {
    Remove-Item "instance\ptsa.db" -Force
    Write-Log "Removed existing production database" "White"
}

# Run comprehensive seeding
Write-Log "Running comprehensive seeding script..." "White"
python comprehensive_seed.py

if ($LASTEXITCODE -ne 0) {
    Write-Log "Comprehensive seeding failed" "Red"
    exit 1
}

if (-not (Test-Path "instance\ptsa_dev.db")) {
    Write-Log "Seeding script did not create database file" "Red"
    exit 1
}

Write-Log "Comprehensive seeding completed successfully" "Green"

# Step 2: Prepare for deployment
Write-Log "Preparing database for deployment..." "Yellow"

# Ensure instance directory exists
if (-not (Test-Path "instance")) {
    New-Item -ItemType Directory -Path "instance" -Force
}

# Copy dev database as production database
Copy-Item "instance\ptsa_dev.db" "instance\ptsa.db" -Force
Write-Log "Database prepared for container deployment" "Green"

# Step 3: Build Docker image
Write-Log "Building Docker image with seeded data..." "Yellow"
docker build -t ptsa-tracker:seeded .

if ($LASTEXITCODE -ne 0) {
    Write-Log "Docker build failed" "Red"
    exit 1
}

Write-Log "Docker image built successfully" "Green"

# Step 4: Tag and push to Azure Container Registry
Write-Log "Pushing to Azure Container Registry..." "Yellow"

# Login to ACR
az acr login --name acrptsa298

if ($LASTEXITCODE -ne 0) {
    Write-Log "ACR login failed" "Red"
    exit 1
}

# Tag and push
docker tag ptsa-tracker:seeded acrptsa298.azurecr.io/ptsa-tracker:latest
docker push acrptsa298.azurecr.io/ptsa-tracker:latest

if ($LASTEXITCODE -ne 0) {
    Write-Log "Docker push failed" "Red"
    exit 1
}

Write-Log "Image pushed successfully" "Green"

# Step 5: Deploy to Azure
Write-Log "Deploying to Azure..." "Yellow"

# Use existing deployment script if available, otherwise deploy directly
if (Test-Path ".\cleanup-and-deploy.ps1") {
    .\cleanup-and-deploy.ps1
} else {
    # Direct deployment
    $RESOURCE_GROUP = "ptsa-rg"
    $WEB_APP_NAME = "ptsa-tracker-webapp"
    
    # Restart web app to pull new image
    Write-Log "Restarting Azure Web App..." "White"
    az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP
    
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Web app restart failed" "Red"
        exit 1
    }
}

# Step 6: Wait and test
Write-Log "Waiting for deployment to complete..." "Yellow"
Start-Sleep -Seconds 60

$APP_URL = "https://ptsa-tracker.azurewebsites.net"

Write-Log "Testing deployed application..." "White"
try {
    $response = Invoke-WebRequest -Uri $APP_URL -TimeoutSec 30 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Log "Application is responding successfully!" "Green"
    } else {
        Write-Log "Application responded with status: $($response.StatusCode)" "Yellow"
    }
} catch {
    Write-Log "Application test failed: $($_.Exception.Message)" "Red"
    Write-Log "The application might still be starting up" "Yellow"
}

Write-Log "Deployment Complete!" "Green"
Write-Log "===================" "Green"
Write-Log "Your PTSA Tracker with comprehensive seeded data is available at:" "Green"
Write-Log "$APP_URL" "Cyan"
Write-Log "" "White"
Write-Log "Login Credentials:" "White"
Write-Log "  Admin: admin@ptsa.co.za / admin123" "White"
Write-Log "" "White"
Write-Log "Sample Companies:" "White"
Write-Log "  Gehring Technologies: admin@gehring.co.za / gehring123" "White"
Write-Log "  ACME Precision: operations@acmeprecision.co.za / acme123" "White"
Write-Log "  Bosch Tooling: info@bosch-tooling.co.za / bosch123" "White"
Write-Log "  Sandvik Tooling: sa.admin@sandvik.com / sandvik123" "White"
Write-Log "  Cape Tool & Engineering: info@capetool.co.za / cape123" "White"
Write-Log "  Durban Tool & Die Works: admin@dtdworks.co.za / durban123" "White"
Write-Log "  Johannesburg Precision Tools: admin@jpttools.co.za / jpt123" "White"
Write-Log "  Atlas Die Casting Solutions: info@atlasdie.co.za / atlas123" "White"
Write-Log "" "White"
Write-Log "Features included:" "White"
Write-Log "  - 8 realistic South African tooling companies" "White"
Write-Log "  - 8 comprehensive improvement measures" "White"
Write-Log "  - 2 years of benchmarking data per company" "White"
Write-Log "  - Realistic assignments and progress tracking" "White"
Write-Log "  - Complete measure history and notifications" "White"
Write-Log "  - Full navigation with all features working" "White"
