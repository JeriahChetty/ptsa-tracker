# Deploy PTSA Tracker to Azure App Service for cleaner URLs

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
$RESOURCE_GROUP = "rg-ptsa-aci-za"
$LOCATION = "southafricanorth"
$ACR_NAME = "acrptsa298"
$APP_SERVICE_PLAN = "ptsa-app-plan"
$WEB_APP_NAME = "ptsa-tracker"  # This will create ptsa-tracker.azurewebsites.net
$CONTAINER_IMAGE = "$ACR_NAME.azurecr.io/ptsa-tracker:latest"

Write-Log "Deploy PTSA Tracker to Azure App Service" "Green"
Write-Log "=========================================" "Green"

# Step 1: Prepare local database
Write-Log "Preparing database..." "Yellow"
if (Test-Path "instance\ptsa_dev.db") {
    if (-not (Test-Path "instance")) {
        New-Item -ItemType Directory -Path "instance" -Force
    }
    Copy-Item "instance\ptsa_dev.db" "instance\ptsa.db" -Force
    Write-Log "Database prepared" "Green"
} else {
    Write-Log "Local database not found. Run comprehensive_seed.py first." "Red"
    exit 1
}

# Step 2: Build and push image
Write-Log "Building and pushing Docker image..." "Yellow"
docker build -t ptsa-tracker:latest .
az acr login --name $ACR_NAME
docker tag ptsa-tracker:latest $CONTAINER_IMAGE
docker push $CONTAINER_IMAGE
Write-Log "Image pushed to registry" "Green"

# Step 3: Create App Service Plan (if it doesn't exist)
Write-Log "Creating App Service Plan..." "Yellow"
az appservice plan create `
    --name $APP_SERVICE_PLAN `
    --resource-group $RESOURCE_GROUP `
    --location $LOCATION `
    --sku B1 `
    --is-linux `
    --tags Project=PTSA-Tracker Environment=Production

# Step 4: Create Web App
Write-Log "Creating Web App..." "Yellow"
az webapp create `
    --resource-group $RESOURCE_GROUP `
    --plan $APP_SERVICE_PLAN `
    --name $WEB_APP_NAME `
    --deployment-container-image-name $CONTAINER_IMAGE `
    --tags Project=PTSA-Tracker Environment=Production

# Step 5: Configure container settings
Write-Log "Configuring container settings..." "Yellow"
az acr update --name $ACR_NAME --admin-enabled true
$ACR_USERNAME = az acr credential show --name $ACR_NAME --query "username" -o tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv

az webapp config container set `
    --name $WEB_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --container-image-name $CONTAINER_IMAGE `
    --container-registry-url "https://$ACR_NAME.azurecr.io" `
    --container-registry-user $ACR_USERNAME `
    --container-registry-password $ACR_PASSWORD

# Step 6: Configure application settings
Write-Log "Configuring application settings..." "Yellow"
az webapp config appsettings set `
    --resource-group $RESOURCE_GROUP `
    --name $WEB_APP_NAME `
    --settings `
    FLASK_ENV=production `
    FLASK_APP=app.py `
    WEBSITES_PORT=5000 `
    WEBSITES_CONTAINER_START_TIME_LIMIT=1800 `
    SCM_DO_BUILD_DURING_DEPLOYMENT=false `
    PYTHONUNBUFFERED=1

# Step 7: Enable HTTPS
Write-Log "Enabling HTTPS..." "Yellow"
az webapp update `
    --name $WEB_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --https-only true

# Step 8: Restart and get URL
Write-Log "Restarting web app..." "Yellow"
az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP

Start-Sleep -Seconds 30

$WEB_APP_URL = az webapp show --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP --query "defaultHostName" -o tsv

Write-Log "Deployment Complete!" "Green"
Write-Log "===================" "Green"
Write-Log "Your PTSA Tracker is now available at:" "Green"
Write-Log "https://$WEB_APP_URL" "Cyan"
Write-Log "" "White"
Write-Log "This is MUCH cleaner than the Container Instance URL!" "Yellow"
Write-Log "" "White"
Write-Log "Login Credentials:" "White"
Write-Log "Admin: admin@ptsa.co.za / admin123" "White"
