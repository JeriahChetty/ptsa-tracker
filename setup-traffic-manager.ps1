# Setup Traffic Manager for custom short URL

$TRAFFIC_MANAGER_PROFILE = "ptsa-tracker-tm"
$RESOURCE_GROUP = "rg-ptsa-aci-za"
$CONTAINER_NAME = "ptsa-tracker-final-3018"

Write-Host "Creating Traffic Manager Profile..." -ForegroundColor Green

# Create Traffic Manager profile
az network traffic-manager profile create `
    --name $TRAFFIC_MANAGER_PROFILE `
    --resource-group $RESOURCE_GROUP `
    --routing-method Priority `
    --unique-dns-name "ptsa-tracker" `
    --ttl 30 `
    --protocol HTTP `
    --port 5000 `
    --path "/"

# Add container as endpoint
$CONTAINER_FQDN = az container show --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP --query "ipAddress.fqdn" -o tsv

az network traffic-manager endpoint create `
    --name "ptsa-container" `
    --profile-name $TRAFFIC_MANAGER_PROFILE `
    --resource-group $RESOURCE_GROUP `
    --type externalEndpoints `
    --target $CONTAINER_FQDN `
    --endpoint-location "South Africa North" `
    --priority 1

Write-Host "Traffic Manager URL: http://ptsa-tracker.trafficmanager.net:5000" -ForegroundColor Cyan
