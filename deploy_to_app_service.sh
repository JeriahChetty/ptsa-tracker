#!/bin/bash

# PTSA Tracker - Azure App Service Deployment Script
# This creates an App Service and deploys your container

set -e

# Configuration
RESOURCE_GROUP="ptsa-rg"
ACR_NAME="ptsatrackerapp"
APP_SERVICE_PLAN="ptsa-plan"
WEB_APP_NAME="ptsa-tracker-webapp"
IMAGE_NAME="ptsa-tracker"
IMAGE_TAG="latest"
LOCATION="southafricanorth"

echo "🌐 PTSA Tracker - Azure App Service Deployment"
echo "=============================================="

# Step 1: Create App Service Plan
echo "📋 Creating App Service Plan..."
az appservice plan create \
    --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku B1 \
    --is-linux \
    --output table

# Step 2: Create Web App
echo "🚀 Creating Web App..."
az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --name $WEB_APP_NAME \
    --deployment-container-image-name $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG \
    --output table

# Step 3: Get ACR credentials
echo "🔐 Getting ACR credentials..."
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query "username" -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

# Step 4: Configure Container Registry Authentication
echo "🔑 Configuring ACR authentication..."
az webapp config container set \
    --name $WEB_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --container-image-name $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG \
    --container-registry-url https://$ACR_NAME.azurecr.io \
    --container-registry-user $ACR_USERNAME \
    --container-registry-password $ACR_PASSWORD

# Step 5: Configure App Settings
echo "⚙️ Configuring app settings..."
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $WEB_APP_NAME \
    --settings \
    FLASK_ENV=production \
    WEBSITES_PORT=5000 \
    WEBSITES_CONTAINER_START_TIME_LIMIT=1800 \
    SCM_DO_BUILD_DURING_DEPLOYMENT=false

# Step 6: Enable Container Logging
echo "📊 Enabling container logging..."
az webapp log config \
    --resource-group $RESOURCE_GROUP \
    --name $WEB_APP_NAME \
    --docker-container-logging filesystem

# Step 7: Restart the app to apply changes
echo "🔄 Restarting web app..."
az webapp restart \
    --resource-group $RESOURCE_GROUP \
    --name $WEB_APP_NAME

# Step 8: Get the app URL
echo "✅ Getting app details..."
APP_URL=$(az webapp show --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --query "defaultHostName" -o tsv)

echo ""
echo "🎉 Deployment Complete!"
echo "=============================================="
echo "🌐 Your PTSA Tracker is available at:"
echo "   https://$APP_URL"
echo ""
echo "📊 Useful commands:"
echo "   View logs: az webapp log tail --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME"
echo "   SSH into container: az webapp ssh --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME"
echo "   Restart app: az webapp restart --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME"
echo ""
echo "🔧 App Service Management:"
echo "   Portal: https://portal.azure.com"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Web App: $WEB_APP_NAME"