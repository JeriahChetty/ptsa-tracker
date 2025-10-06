#!/bin/bash

# PTSA Tracker - Quick Container Deployment Script
# This deploys directly to Azure Container Instances (no App Service needed)

set -e

# Configuration
RESOURCE_GROUP="ptsa-rg"
ACR_NAME="ptsatrackerapp"
CONTAINER_NAME="ptsa-tracker-app"
IMAGE_NAME="ptsa-tracker"
IMAGE_TAG="latest"
LOCATION="southafricanorth"

echo "🚀 PTSA Tracker - Quick Container Deployment"
echo "============================================="

# Get ACR credentials
echo "🔐 Getting ACR credentials..."
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query "username" -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"

echo "📦 Deploying container to Azure Container Instances..."
az container create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --image $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG \
    --cpu 1 \
    --memory 1.5 \
    --registry-login-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --ip-address Public \
    --ports 5000 \
    --location $LOCATION \
    --environment-variables FLASK_ENV=production

echo "✅ Getting container details..."
az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query "{FQDN:ipAddress.fqdn,ProvisioningState:provisioningState}" --output table

echo ""
echo "🎉 Deployment complete!"
echo "🌐 Your app should be available at the FQDN shown above on port 5000"
echo "📊 Check logs with: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"