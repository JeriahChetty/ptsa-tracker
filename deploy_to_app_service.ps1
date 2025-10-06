# PTSA Tracker - Azure App Service Deployment Script (PowerShell)
# This creates an App Service and deploys your container

# Configuration
$RESOURCE_GROUP = "ptsa-rg"
$ACR_NAME = "ptsatrackerapp"
$APP_SERVICE_PLAN = "ptsa-plan"
$WEB_APP_NAME = "ptsa-tracker-webapp"
$IMAGE_NAME = "ptsa-tracker"
$IMAGE_TAG = "latest"
$LOCATION = "southafricanorth"

Write-Host "🌐 PTSA Tracker - Azure App Service Deployment" -ForegroundColor Green
Write-Host "=============================================="

# Step 1: Create App Service Plan
Write-Host "📋 Creating App Service Plan..." -ForegroundColor Yellow
az appservice plan create `
    --name $APP_SERVICE_PLAN `
    --resource-group $RESOURCE_GROUP `
    --location $LOCATION `
    --sku B1 `
    --is-linux `
    --output table

# Step 2: Create Web App
Write-Host "🚀 Creating Web App..." -ForegroundColor Yellow
az webapp create `
    --resource-group $RESOURCE_GROUP `
    --plan $APP_SERVICE_PLAN `
    --name $WEB_APP_NAME `
    --deployment-container-image-name "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$IMAGE_TAG" `
    --output table

# Step 3: Get ACR credentials
Write-Host "🔐 Getting ACR credentials..." -ForegroundColor Yellow
$ACR_USERNAME = az acr credential show --name $ACR_NAME --query "username" -o tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv

# Step 4: Configure Container Registry Authentication
Write-Host "🔑 Configuring ACR authentication..." -ForegroundColor Yellow
az webapp config container set `
    --name $WEB_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --container-image-name "$ACR_NAME.azurecr.io/$IMAGE_NAME`:$IMAGE_TAG" `
    --container-registry-url "https://$ACR_NAME.azurecr.io" `
    --container-registry-user $ACR_USERNAME `
    --container-registry-password $ACR_PASSWORD

# Step 5: Configure App Settings
Write-Host "⚙️ Configuring app settings..." -ForegroundColor Yellow
az webapp config appsettings set `
    --resource-group $RESOURCE_GROUP `
    --name $WEB_APP_NAME `
    --settings `
    FLASK_ENV=production `
    WEBSITES_PORT=5000 `
    WEBSITES_CONTAINER_START_TIME_LIMIT=1800 `
    SCM_DO_BUILD_DURING_DEPLOYMENT=false

# Step 6: Enable Container Logging
Write-Host "📊 Enabling container logging..." -ForegroundColor Yellow
az webapp log config `
    --resource-group $RESOURCE_GROUP `
    --name $WEB_APP_NAME `
    --docker-container-logging filesystem

# Step 7: Restart the app to apply changes
Write-Host "🔄 Restarting web app..." -ForegroundColor Yellow
az webapp restart `
    --resource-group $RESOURCE_GROUP `
    --name $WEB_APP_NAME

# Step 8: Get the app URL
Write-Host "✅ Getting app details..." -ForegroundColor Yellow
$APP_URL = az webapp show --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --query "defaultHostName" -o tsv

Write-Host ""
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "=============================================="
Write-Host "🌐 Your PTSA Tracker is available at:" -ForegroundColor Green
Write-Host "   https://$APP_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Useful commands:" -ForegroundColor Green
Write-Host "   View logs: az webapp log tail --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME"
Write-Host "   SSH into container: az webapp ssh --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME"
Write-Host "   Restart app: az webapp restart --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME"
Write-Host ""
Write-Host "🔧 App Service Management:" -ForegroundColor Green
Write-Host "   Portal: https://portal.azure.com"
Write-Host "   Resource Group: $RESOURCE_GROUP"
Write-Host "   Web App: $WEB_APP_NAME"