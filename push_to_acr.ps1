# Azure Container Registry Push Script for PTSA Tracker (PowerShell)
# Make sure you're logged in to Azure CLI: az login

# Configuration
$RESOURCE_GROUP = "ptsa-rg"
$ACR_NAME = "ptsatrackerapp"
$IMAGE_NAME = "ptsa-tracker"
$IMAGE_TAG = "latest"
$LOCATION = "southafricanorth"

Write-Host "🚀 PTSA Tracker - Azure Container Registry Push" -ForegroundColor Green
Write-Host "=============================================="

# Step 1: Create resource group if it doesn't exist
Write-Host "📦 Creating resource group..." -ForegroundColor Yellow
az group create --name $RESOURCE_GROUP --location $LOCATION --output table

# Step 2: Create Azure Container Registry if it doesn't exist
Write-Host "🏗️  Creating Azure Container Registry..." -ForegroundColor Yellow
az acr create `
    --resource-group $RESOURCE_GROUP `
    --name $ACR_NAME `
    --sku Basic `
    --location $LOCATION `
    --output table

# Step 3: Login to ACR
Write-Host "🔐 Logging into Azure Container Registry..." -ForegroundColor Yellow
az acr login --name $ACR_NAME

# Step 4: Get ACR login server
$ACR_LOGIN_SERVER = az acr show --name $ACR_NAME --query loginServer --output tsv
Write-Host "📍 ACR Login Server: $ACR_LOGIN_SERVER" -ForegroundColor Cyan

# Step 5: Tag the local image
Write-Host "🏷️  Tagging Docker image..." -ForegroundColor Yellow
docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}"
docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:v1.0"

# Step 6: Push the image
Write-Host "📤 Pushing Docker image to ACR..." -ForegroundColor Yellow
docker push "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}"
docker push "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:v1.0"

# Step 7: Verify the push
Write-Host "✅ Verifying push..." -ForegroundColor Yellow
az acr repository list --name $ACR_NAME --output table
az acr repository show-tags --name $ACR_NAME --repository $IMAGE_NAME --output table

Write-Host ""
Write-Host "🎉 Success! Your image is now available at:" -ForegroundColor Green
Write-Host "   ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}" -ForegroundColor Cyan
Write-Host "   ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:v1.0" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔗 Next steps:" -ForegroundColor Green
Write-Host "   - Deploy to Azure Container Instances: az container create"
Write-Host "   - Deploy to Azure App Service: az webapp create"
Write-Host "   - Deploy to Azure Kubernetes Service: kubectl apply"