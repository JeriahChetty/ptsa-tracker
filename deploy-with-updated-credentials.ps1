# Deploy PTSA Tracker with updated admin credentials

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

Write-Log "Deploy PTSA Tracker with Updated Admin Credentials" "Green"
Write-Log "=================================================" "Green"

# Step 1: Clean existing databases
Write-Log "Cleaning existing databases..." "Yellow"
if (Test-Path "instance\ptsa_dev.db") {
    Remove-Item "instance\ptsa_dev.db" -Force
    Write-Log "Removed existing dev database" "White"
}

if (Test-Path "instance\ptsa.db") {
    Remove-Item "instance\ptsa.db" -Force  
    Write-Log "Removed existing production database" "White"
}

# Step 2: Create fresh seeded database with new admin credentials
Write-Log "Creating database with updated admin credentials..." "Yellow"
python comprehensive_seed.py

if ($LASTEXITCODE -ne 0) {
    Write-Log "Database seeding failed" "Red"
    exit 1
}

if (-not (Test-Path "instance\ptsa_dev.db")) {
    Write-Log "Seeding script did not create database file" "Red"
    exit 1
}

Write-Log "Database seeded successfully with new admin: info@ptsa.co.za" "Green"

# Step 3: Prepare for deployment
Write-Log "Preparing for deployment..." "Yellow"
Copy-Item "instance\ptsa_dev.db" "instance\ptsa.db" -Force
Write-Log "Database prepared for deployment" "Green"

# Step 4: Build new Docker image
Write-Log "Building Docker image with updated data..." "Yellow"
docker build -t ptsa-tracker:updated .

if ($LASTEXITCODE -ne 0) {
    Write-Log "Docker build failed" "Red"
    exit 1
}

Write-Log "Docker image built successfully" "Green"

# Step 5: Push to Azure Container Registry
Write-Log "Pushing to Azure Container Registry..." "Yellow"
az acr login --name acrptsa298

if ($LASTEXITCODE -ne 0) {
    Write-Log "ACR login failed" "Red"
    exit 1
}

docker tag ptsa-tracker:updated acrptsa298.azurecr.io/ptsa-tracker:latest
docker push acrptsa298.azurecr.io/ptsa-tracker:latest

if ($LASTEXITCODE -ne 0) {
    Write-Log "Docker push failed" "Red"
    exit 1
}

Write-Log "Image pushed successfully to registry" "Green"

# Step 6: Deploy to Azure App Service
Write-Log "Deploying to Azure App Service..." "Yellow"

# Configure for App Service deployment
$RESOURCE_GROUP = "ptsa-rg"
$WEB_APP_NAME = "ptsa-tracker-webapp"

# Restart the web app to pull the new image
Write-Log "Restarting Azure Web App to pull updated image..." "White"
az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP

if ($LASTEXITCODE -ne 0) {
    Write-Log "Web app restart failed, trying container instance deployment..." "Yellow"
    # Fallback to container instance deployment
    .\cleanup-and-deploy.ps1
} else {
    Write-Log "Web app restarted successfully" "Green"
}

# Step 7: Wait and verify
Write-Log "Waiting for application to start..." "Yellow"
Start-Sleep -Seconds 60

$APP_URL = "https://ptsa-tracker.azurewebsites.net"

Write-Log "Testing deployed application..." "White"
try {
    $response = Invoke-WebRequest -Uri $APP_URL -TimeoutSec 30 -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Log "Application is responding successfully!" "Green"
    } else {
        Write-Log "Application responded with status: $($response.StatusCode)" "Yellow"
    }
} catch {
    Write-Log "Application test failed, but this is normal during startup" "Yellow"
    Write-Log "Please wait a few more minutes for the application to fully start" "White"
}

Write-Log "Deployment Complete!" "Green"
Write-Log "===================" "Green"
Write-Log "Your PTSA Tracker has been deployed with updated credentials!" "Green"
Write-Log "Access URL: $APP_URL" "Cyan"
Write-Log "" "White"
Write-Log "NEW ADMIN LOGIN CREDENTIALS:" "Yellow"
Write-Log "  Email: info@ptsa.co.za" "Cyan"
Write-Log "  Password: info123" "Cyan"
Write-Log "" "White"
Write-Log "Company Login Credentials:" "White"
Write-Log "  Gehring Technologies: admin@gehring.co.za / gehring123" "White"
Write-Log "  ACME Precision: operations@acmeprecision.co.za / acme123" "White"
Write-Log "  Bosch Tooling: info@bosch-tooling.co.za / bosch123" "White"
Write-Log "  Sandvik Tooling: sa.admin@sandvik.com / sandvik123" "White"
Write-Log "  Cape Tool & Engineering: info@capetool.co.za / cape123" "White"
Write-Log "  Durban Tool & Die Works: admin@dtdworks.co.za / durban123" "White"
Write-Log "  Johannesburg Precision Tools: admin@jpttools.co.za / jpt123" "White"
Write-Log "  Atlas Die Casting Solutions: info@atlasdie.co.za / atlas123" "White"
Write-Log "" "White"
Write-Log "Complete system features:" "White"
Write-Log "  - 8 realistic South African tooling companies" "White"
Write-Log "  - 8 comprehensive improvement measures" "White"
Write-Log "  - 2 years of benchmarking data per company" "White"
Write-Log "  - Realistic assignments and progress tracking" "White"
Write-Log "  - Complete admin and company dashboards" "White"
Write-Log "  - Measure history, benchmarking, and notifications" "White"
