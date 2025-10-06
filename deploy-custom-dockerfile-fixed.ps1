# PTSA Tracker - Custom Dockerfile Azure Deployment (CORRECTED)
# This script builds from Dockerfile and deploys to Azure App Service

# ============================================
# Configuration Variables
# ============================================
$RESOURCE_GROUP = "ptsa-rg"
$LOCATION = "southafricanorth"
$ACR_NAME = "ptsatrackerapp"
$APP_SERVICE_PLAN = "ptsa-plan"
$WEB_APP_NAME = "ptsa-tracker-webapp"
$CONTAINER_IMAGE = "$ACR_NAME.azurecr.io/ptsa-tracker:latest"

Write-Host "🐳 PTSA Tracker - Custom Dockerfile Deployment" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# ============================================
# Step 1: Build from Custom Dockerfile
# ============================================
Write-Host "`n🔨 Step 1: Building from Custom Dockerfile..." -ForegroundColor Yellow

# Check if Dockerfile exists
if (Test-Path "Dockerfile") {
    Write-Host "✅ Dockerfile found" -ForegroundColor Green
} else {
    Write-Host "❌ Dockerfile not found in current directory" -ForegroundColor Red
    Write-Host "Make sure you're in the project root directory" -ForegroundColor Yellow
    exit 1
}

# Build Docker image
Write-Host "🔨 Building Docker image locally..." -ForegroundColor White
docker build -t ptsa-tracker:latest .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Docker image built successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    exit 1
}

# ============================================
# Step 2: Push to Azure Container Registry
# ============================================
Write-Host "`n📤 Step 2: Pushing to Azure Container Registry..." -ForegroundColor Yellow

# Login to ACR
Write-Host "🔐 Logging into ACR..." -ForegroundColor White
az acr login --name $ACR_NAME

# Tag for ACR
Write-Host "🏷️ Tagging image..." -ForegroundColor White
docker tag ptsa-tracker:latest $CONTAINER_IMAGE

# Push to ACR
Write-Host "📤 Pushing image to ACR..." -ForegroundColor White
docker push $CONTAINER_IMAGE

Write-Host "✅ Image pushed to ACR" -ForegroundColor Green

# ============================================
# Step 3: Create App Service Plan
# ============================================
Write-Host "`n📋 Step 3: Creating App Service Plan..." -ForegroundColor Yellow

az appservice plan create `
    --name $APP_SERVICE_PLAN `
    --resource-group $RESOURCE_GROUP `
    --location $LOCATION `
    --sku B1 `
    --is-linux

Write-Host "✅ App Service Plan created" -ForegroundColor Green

# ============================================
# Step 4: Create Web App
# ============================================
Write-Host "`n🌐 Step 4: Creating Web App..." -ForegroundColor Yellow

az webapp create `
    --resource-group $RESOURCE_GROUP `
    --plan $APP_SERVICE_PLAN `
    --name $WEB_APP_NAME `
    --deployment-container-image-name $CONTAINER_IMAGE

Write-Host "✅ Web App created" -ForegroundColor Green

# ============================================
# Step 5: Configure Container Registry
# ============================================
Write-Host "`n🔑 Step 5: Configuring Container Registry..." -ForegroundColor Yellow

# Enable ACR admin
Write-Host "🔐 Enabling ACR admin access..." -ForegroundColor White
az acr update --name $ACR_NAME --admin-enabled true

# Get credentials
Write-Host "🔑 Getting ACR credentials..." -ForegroundColor White
$ACR_USERNAME = az acr credential show --name $ACR_NAME --query "username" -o tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv

# Configure container settings
Write-Host "⚙️ Configuring container settings..." -ForegroundColor White
az webapp config container set `
    --name $WEB_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --container-image-name $CONTAINER_IMAGE `
    --container-registry-url https://$ACR_NAME.azurecr.io `
    --container-registry-user $ACR_USERNAME `
    --container-registry-password $ACR_PASSWORD

# Enable continuous deployment
Write-Host "🔄 Enabling continuous deployment..." -ForegroundColor White
az webapp deployment container config `
    --name $WEB_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --enable-cd true

Write-Host "✅ Container registry configured" -ForegroundColor Green

# ============================================
# Step 6: Configure Application Settings
# ============================================
Write-Host "`n⚙️ Step 6: Configuring Application..." -ForegroundColor Yellow

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

Write-Host "✅ Application configured" -ForegroundColor Green

# ============================================
# Step 7: Enable HTTPS & Security
# ============================================
Write-Host "`n🔒 Step 7: Enabling Security..." -ForegroundColor Yellow

az webapp update `
    --name $WEB_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --https-only true

az webapp config set `
    --resource-group $RESOURCE_GROUP `
    --name $WEB_APP_NAME `
    --min-tls-version 1.2

Write-Host "✅ Security configured" -ForegroundColor Green

# ============================================
# Step 8: Final Deployment
# ============================================
Write-Host "`n🚀 Step 8: Final Deployment..." -ForegroundColor Yellow

# Restart app
Write-Host "🔄 Restarting web app..." -ForegroundColor White
az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP

# Wait for startup
Write-Host "⏳ Waiting for application to start..." -ForegroundColor White
Start-Sleep -Seconds 30

# Get URL
$WEB_APP_URL = az webapp show --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP --query "defaultHostName" -o tsv

# ============================================
# Deployment Complete
# ============================================
Write-Host "`n🎉 Custom Dockerfile Deployment Complete!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host "🌐 Your PTSA Tracker is available at:" -ForegroundColor Green
Write-Host "   https://$WEB_APP_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "🐳 Container Details:" -ForegroundColor Green
Write-Host "   Registry: $ACR_NAME.azurecr.io" -ForegroundColor White
Write-Host "   Image: ptsa-tracker:latest" -ForegroundColor White
Write-Host "   Built from: Custom Dockerfile" -ForegroundColor White
Write-Host ""
Write-Host "📊 Management Commands:" -ForegroundColor Green
Write-Host "   View logs: az webapp log tail --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME" -ForegroundColor White
Write-Host "   Restart: az webapp restart --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME" -ForegroundColor White
Write-Host "   SSH: az webapp ssh --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME" -ForegroundColor White