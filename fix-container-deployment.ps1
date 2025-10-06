# Fix container deployment with proper Flask configuration

param(
    [string]$ResourceGroupName = "rg-ptsa-aci-za",
    [string]$Location = "South Africa North",
    [string]$ContainerName = "ptsa-tracker-za-fixed-$(Get-Random -Maximum 9999)"
)

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

Write-Log "Fixing container deployment..." "Green"

# Use existing ACR
$acrLoginServer = "acrptsa298.azurecr.io"
$imageToUse = "$acrLoginServer/ptsa-tracker:latest"

# Get ACR credentials
$acrCredsJson = az acr credential show --name "acrptsa298"
$acrCreds = $acrCredsJson | ConvertFrom-Json
$acrUsername = $acrCreds.username
$passwords = $acrCreds.passwords
$acrPassword = $passwords[0].value

# Fixed environment variables with proper Flask configuration
$envVars = @(
    "FLASK_ENV=production",
    "FLASK_APP=app.py",
    "DATABASE_URL=sqlite:///app/instance/ptsa.db",
    "SECRET_KEY=ptsa-secret-$(Get-Random)",
    "PYTHONUNBUFFERED=1",
    "PORT=5000"
)

Write-Log "Creating fixed container..." "Yellow"

az container create `
    --resource-group $ResourceGroupName `
    --name $ContainerName `
    --image $imageToUse `
    --registry-username $acrUsername `
    --registry-password $acrPassword `
    --dns-name-label $ContainerName `
    --ports 5000 `
    --cpu 1 `
    --memory 1.5 `
    --os-type Linux `
    --restart-policy Always `
    --environment-variables $envVars `
    --command-line "python -m flask run --host=0.0.0.0 --port=5000" `
    --location $Location

if ($LASTEXITCODE -eq 0) {
    $fqdn = az container show --resource-group $ResourceGroupName --name $ContainerName --query ipAddress.fqdn --output tsv
    
    Write-Log "" "White"
    Write-Log "FIXED CONTAINER DEPLOYED!" "Green"
    Write-Log "=========================" "Green"
    Write-Log "URL: http://$fqdn`:5000" "Cyan"
    Write-Log "Container: $ContainerName" "White"
    
    Write-Log "" "White"
    Write-Log "Wait 2-3 minutes for the container to fully start, then test the URL." "Yellow"
} else {
    Write-Log "Failed to create fixed container" "Red"
}
