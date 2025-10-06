#!/bin/bash

# Azure Container Registry Push Script for PTSA Tracker
# Make sure you're logged in to Azure CLI: az login

set -e

# Configuration
RESOURCE_GROUP="ptsa-rg"
ACR_NAME="ptsatrackerapp"
IMAGE_NAME="ptsa-tracker"
IMAGE_TAG="latest"
LOCATION="southafricanorth"

echo "🚀 PTSA Tracker - Azure Container Registry Push"
echo "=============================================="

# Step 1: Create resource group if it doesn't exist
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION --output table

# Step 2: Create Azure Container Registry if it doesn't exist
echo "🏗️  Creating Azure Container Registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --location $LOCATION \
    --output table

# Step 3: Login to ACR
echo "🔐 Logging into Azure Container Registry..."
az acr login --name $ACR_NAME

# Step 4: Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
echo "📍 ACR Login Server: $ACR_LOGIN_SERVER"

# Step 5: Tag the local image
echo "🏷️  Tagging Docker image..."
docker tag $IMAGE_NAME:$IMAGE_TAG $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG
docker tag $IMAGE_NAME:$IMAGE_TAG $ACR_LOGIN_SERVER/$IMAGE_NAME:v1.0

# Step 6: Push the image
echo "📤 Pushing Docker image to ACR..."
docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG
docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:v1.0

# Step 7: Verify the push
echo "✅ Verifying push..."
az acr repository list --name $ACR_NAME --output table
az acr repository show-tags --name $ACR_NAME --repository $IMAGE_NAME --output table

echo ""
echo "🎉 Success! Your image is now available at:"
echo "   $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG"
echo "   $ACR_LOGIN_SERVER/$IMAGE_NAME:v1.0"
echo ""
echo "🔗 Next steps:"
echo "   - Deploy to Azure Container Instances: az container create"
echo "   - Deploy to Azure App Service: az webapp create"
echo "   - Deploy to Azure Kubernetes Service: kubectl apply"