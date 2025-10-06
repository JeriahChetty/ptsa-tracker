# Alternative deployment using Azure Container Instances (no quota limits)

param(
    [string]$ResourceGroupName = "rg-ptsa-tracker-aci",
    [string]$Location = "East US",
    [string]$ContainerName = "ptsa-tracker-$(Get-Random -Maximum 9999)",
    [string]$ACRName = "acrptsatracker"
)

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

Write-Log "🐳 Starting Azure Container Instances deployment..." "Green"

# 1) Login check
try {
    $ctx = az account show 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Azure login required. Run: az login" }
    $ctxObj = $ctx | ConvertFrom-Json
    Write-Log ("Logged in as: {0}" -f $ctxObj.user.name) "Green"
} catch {
    Write-Log $_ "Red"
    exit 1
}

# 2) Create resource group
Write-Log "Creating resource group..." "Yellow"
az group create --name $ResourceGroupName --location $Location | Out-Null

# 3) Get ACR credentials
Write-Log "Getting ACR credentials..." "Yellow"
$acrLoginServer = az acr show --name $ACRName --query loginServer --output tsv
$acrUsername = az acr credential show --name $ACRName --query username --output tsv
$acrPassword = az acr credential show --name $ACRName --query "passwords[0].value" --output tsv

# 4) Deploy container instance
Write-Log "Deploying container instance..." "Yellow"
az container create `
    --resource-group $ResourceGroupName `
    --name $ContainerName `
    --image "$acrLoginServer/ptsa-tracker:latest" `
    --registry-username $acrUsername `
    --registry-password $acrPassword `
    --dns-name-label $ContainerName `
    --ports 5000 `
    --environment-variables `
        FLASK_ENV=production `
        FLASK_APP=app.py `
        DATABASE_URL="sqlite:///instance/ptsa.db" `
        SECRET_KEY="your-secret-key-here"

if ($LASTEXITCODE -eq 0) {
    # Get the FQDN
    $fqdn = az container show --resource-group $ResourceGroupName --name $ContainerName --query ipAddress.fqdn --output tsv
    
    Write-Log "🎉 Container deployed successfully!" "Green"
    Write-Log "URL: http://$fqdn:5000" "Cyan"
    Write-Log "Note: This uses HTTP (not HTTPS) and is suitable for testing only" "Yellow"
} else {
    Write-Log "❌ Container deployment failed" "Red"
}
