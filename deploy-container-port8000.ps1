# Deploy container with port 8000 (sometimes more reliable)

param(
    [string]$ResourceGroupName = "rg-ptsa-aci-za",
    [string]$Location = "South Africa North",
    [string]$ContainerName = "ptsa-tracker-za-8000-$(Get-Random -Maximum 9999)"
)

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

Write-Log "Deploying container with port 8000..." "Green"

# Use existing ACR
$acrLoginServer = "acrptsa298.azurecr.io"
$imageToUse = "$acrLoginServer/ptsa-tracker:latest"

# Get ACR credentials
$acrCredsJson = az acr credential show --name "acrptsa298"
$acrCreds = $acrCredsJson | ConvertFrom-Json
$acrUsername = $acrCreds.username
$passwords = $acrCreds.passwords
$acrPassword = $passwords[0].value

# Environment variables for port 8000
$envVars = @(
    "FLASK_ENV=production",
    "FLASK_APP=app.py",
    "DATABASE_URL=sqlite:///app/instance/ptsa.db",
    "SECRET_KEY=ptsa-secret-$(Get-Random)",
    "PYTHONUNBUFFERED=1",
    "PORT=8000"
)

Write-Log "Creating container on port 8000..." "Yellow"

az container create `
    --resource-group $ResourceGroupName `
    --name $ContainerName `
    --image $imageToUse `
    --registry-username $acrUsername `
    --registry-password $acrPassword `
    --dns-name-label $ContainerName `
    --ports 8000 `
    --cpu 1 `
    --memory 1.5 `
    --os-type Linux `
    --restart-policy Always `
    --environment-variables $envVars `
    --command-line "python -m flask run --host=0.0.0.0 --port=8000" `
    --location $Location

if ($LASTEXITCODE -eq 0) {
    $fqdn = az container show --resource-group $ResourceGroupName --name $ContainerName --query ipAddress.fqdn --output tsv
    
    Write-Log "" "White"
    Write-Log "CONTAINER DEPLOYED ON PORT 8000!" "Green"
    Write-Log "=================================" "Green"
    Write-Log "URL: http://$fqdn`:8000" "Cyan"
    Write-Log "Container: $ContainerName" "White"
} else {
    Write-Log "Failed to create container" "Red"
}
