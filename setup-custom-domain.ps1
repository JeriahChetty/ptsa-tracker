# Setup custom domain for PTSA Tracker

# Example: If you own ptsa.co.za domain
$DOMAIN_NAME = "tracker.ptsa.co.za"  # Replace with your actual domain
$CONTAINER_NAME = "ptsa-tracker-final-3018"
$RESOURCE_GROUP = "rg-ptsa-aci-za"

Write-Host "Setting up custom domain: $DOMAIN_NAME" -ForegroundColor Green

# Get the container's public IP
$PUBLIC_IP = az container show --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP --query "ipAddress.ip" -o tsv

Write-Host "Container IP: $PUBLIC_IP" -ForegroundColor Yellow
Write-Host "" -ForegroundColor White
Write-Host "To use your custom domain, add this DNS record:" -ForegroundColor Cyan
Write-Host "Type: A" -ForegroundColor White
Write-Host "Name: tracker (or your subdomain)" -ForegroundColor White
Write-Host "Value: $PUBLIC_IP" -ForegroundColor White
Write-Host "TTL: 300" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "After DNS propagation, access via: http://$DOMAIN_NAME:5000" -ForegroundColor Green
