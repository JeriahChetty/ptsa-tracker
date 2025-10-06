# Deploy PTSA Tracker with seeded data to Azure App Service

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

# Configuration
$RESOURCE_GROUP = "ptsa-rg"
$LOCATION = "southafricanorth"
$ACR_NAME = "ptsatrackerapp"
$APP_SERVICE_PLAN = "ptsa-plan"
$WEB_APP_NAME = "ptsa-tracker-webapp"
$CONTAINER_IMAGE = "$ACR_NAME.azurecr.io/ptsa-tracker:latest"

Write-Log "Deploy PTSA Tracker with Seeded Data to Azure App Service" "Green"
Write-Log "=========================================================" "Green"

# Step 1: Ensure we have seeded data locally
Write-Log "Checking for local seeded database..." "Yellow"
if (-not (Test-Path "instance\ptsa_dev.db")) {
    Write-Log "No seeded database found. Creating one now..." "Yellow"
    python comprehensive_seed.py
    
    if (-not (Test-Path "instance\ptsa_dev.db")) {
        Write-Log "Failed to create seeded database" "Red"
        exit 1
    }
}

# Step 2: Prepare database for production
Write-Log "Preparing database for production deployment..." "Yellow"
if (-not (Test-Path "instance")) {
    New-Item -ItemType Directory -Path "instance" -Force
}
Copy-Item "instance\ptsa_dev.db" "instance\ptsa.db" -Force
Write-Log "Database prepared" "Green"

# Step 3: Build Docker image with seeded data
Write-Log "Building Docker image with seeded data..." "Yellow"
docker build -t ptsa-tracker:with-data .

if ($LASTEXITCODE -ne 0) {
    Write-Log "Docker build failed" "Red"
    exit 1
}

# Step 4: Push to Azure Container Registry
Write-Log "Pushing to Azure Container Registry..." "Yellow"
az acr login --name $ACR_NAME

if ($LASTEXITCODE -ne 0) {
    Write-Log "ACR login failed" "Red"
    exit 1
}

docker tag ptsa-tracker:with-data $CONTAINER_IMAGE
docker push $CONTAINER_IMAGE

Write-Log "Image pushed successfully" "Green"

# Step 5: Update the web app container settings
Write-Log "Updating web app container settings..." "Yellow"

# Get ACR credentials
$ACR_USERNAME = az acr credential show --name $ACR_NAME --query "username" -o tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv

# Update container settings
az webapp config container set `
    --name $WEB_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --container-image-name $CONTAINER_IMAGE `
    --container-registry-url "https://$ACR_NAME.azurecr.io" `
    --container-registry-user $ACR_USERNAME `
    --container-registry-password $ACR_PASSWORD

# Step 6: Restart the web app
Write-Log "Restarting web app..." "Yellow"
az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP

# Step 7: Wait and test
Write-Log "Waiting for application to start..." "Yellow"
Start-Sleep -Seconds 45

$WEB_APP_URL = "https://ptsa-tracker.azurewebsites.net"

Write-Log "Testing application..." "Yellow"
try {
    $response = Invoke-WebRequest -Uri $WEB_APP_URL -TimeoutSec 30 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Log "Application is responding!" "Green"
    } else {
        Write-Log "Application responded with status: $($response.StatusCode)" "Yellow"
    }
} catch {
    Write-Log "Application test failed: $($_.Exception.Message)" "Red"
    Write-Log "The app might still be starting up. Please wait a few more minutes." "Yellow"
}

Write-Log "Deployment Complete!" "Green"
Write-Log "====================" "Green"
Write-Log "Your PTSA Tracker with comprehensive seeded data is available at:" "Green"
Write-Log "$WEB_APP_URL" "Cyan"
Write-Log "" "White"
Write-Log "Login Credentials:" "White"
Write-Log "  Admin: admin@ptsa.co.za / admin123" "White"
Write-Log "" "White"
Write-Log "Sample Companies:" "White"
Write-Log "  Gehring Technologies: admin@gehring.co.za / gehring123" "White"
Write-Log "  ACME Precision: operations@acmeprecision.co.za / acme123" "White"
Write-Log "  Bosch Tooling: info@bosch-tooling.co.za / bosch123" "White"
Write-Log "  Sandvik Tooling: sa.admin@sandvik.com / sandvik123" "White"
Write-Log "  And 4 more companies with realistic data!" "White"
Write-Log "" "White"
Write-Log "Features included:" "White"
Write-Log "  - 8 realistic South African tooling companies" "White"
Write-Log "  - 8 comprehensive improvement measures" "White"
Write-Log "  - 2 years of benchmarking data per company" "White"
Write-Log "  - Realistic assignments and progress tracking" "White"
Write-Log "  - Complete measure history and notifications" "White"
