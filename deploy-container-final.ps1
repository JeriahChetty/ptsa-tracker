# Azure Container Instances deployment with automatic resource provider registration

param(
    [string]$ResourceGroupName = "rg-ptsa-aci-za",
    [string]$Location = "South Africa North",
    [string]$ContainerName = "ptsa-tracker-za-$(Get-Random -Maximum 9999)",
    [string]$ACRName = "acrptsa$(Get-Random -Maximum 999)"
)

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

Write-Log "Azure Container Instances deployment for South Africa" "Green"
Write-Log "=======================================================" "Green"

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

# 2) Register required resource providers
Write-Log "Registering required Azure resource providers..." "Yellow"
try {
    Write-Log "Registering Microsoft.ContainerInstance..." "White"
    az provider register --namespace Microsoft.ContainerInstance --wait
    
    Write-Log "Registering Microsoft.ContainerRegistry..." "White"
    az provider register --namespace Microsoft.ContainerRegistry --wait
    
    Write-Log "Resource providers registered successfully." "Green"
} catch {
    Write-Log "Warning: Some resource providers may not be registered. Continuing..." "Yellow"
}

# 3) Create resource group
Write-Log "Creating resource group in South Africa North..." "Yellow"
az group create --name $ResourceGroupName --location $Location | Out-Null

# 4) Use the existing ACR (acrptsa298.azurecr.io)
$acrLoginServer = "acrptsa298.azurecr.io"
$imageToUse = "$acrLoginServer/ptsa-tracker:latest"

try {
    Write-Log "Using existing ACR: $acrLoginServer" "Green"
    
    # Get ACR credentials with proper error handling
    $acrCredsJson = az acr credential show --name "acrptsa298"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to retrieve ACR credentials"
    }
    
    $acrCreds = $acrCredsJson | ConvertFrom-Json
    $acrUsername = $acrCreds.username
    # Fix the array indexing issue with proper PowerShell array access
    $passwords = $acrCreds.passwords
    $acrPassword = $passwords[0].value
    
    Write-Log "ACR credentials obtained" "Green"
} catch {
    Write-Log "Failed to get ACR credentials: $_" "Red"
    exit 1
}

# 5) Deploy container instance
Write-Log "Deploying container instance..." "Yellow"

$envVars = @(
    "FLASK_ENV=production",
    "FLASK_APP=app.py",
    "DATABASE_URL=sqlite:///tmp/ptsa.db",
    "SECRET_KEY=ptsa-secret-$(Get-Random)",
    "MAIL_SERVER=mail.ptsa.co.za",
    "MAIL_PORT=587",
    "MAIL_USE_TLS=False",
    "MAIL_USE_SSL=False",
    "MAIL_USERNAME=info@ptsa.co.za",
    "MAIL_PASSWORD=wqMvrJm4VZp",
    "MAIL_DEFAULT_SENDER=PTSA Tracker <info@ptsa.co.za>"
)

try {
    Write-Log "Creating container with Flask app image..." "White"
    
    az container create `
        --resource-group $ResourceGroupName `
        --name $ContainerName `
        --image $imageToUse `
        --registry-username $acrUsername `
        --registry-password $acrPassword `
        --dns-name-label $ContainerName `
        --ports 5000 `
        --cpu 1 `
        --memory 1 `
        --os-type Linux `
        --restart-policy Always `
        --environment-variables $envVars `
        --location $Location | Out-Null

    if ($LASTEXITCODE -eq 0) {
        # Get the FQDN
        $fqdn = az container show --resource-group $ResourceGroupName --name $ContainerName --query ipAddress.fqdn --output tsv
        
        Write-Log "" "White"
        Write-Log "CONTAINER DEPLOYMENT SUCCESSFUL!" "Green"
        Write-Log "===================================" "Green"
        Write-Log "URL: http://$fqdn`:5000" "Cyan"
        Write-Log "Region: $Location" "White"
        Write-Log "Container: $ContainerName" "White"
        Write-Log "" "White"
        
        Write-Log "Default login:" "Yellow"
        Write-Log "   Email: admin@ptsa.co.za" "White"
        Write-Log "   Password: admin123" "White"
        Write-Log "   IMPORTANT: Change these credentials after first login!" "Red"
        
        Write-Log "" "White"
        Write-Log "Management:" "Yellow"
        Write-Log "   View logs: az container logs --name $ContainerName --resource-group $ResourceGroupName" "White"
        Write-Log "   Restart: az container restart --name $ContainerName --resource-group $ResourceGroupName" "White"
        Write-Log "   Delete: az container delete --name $ContainerName --resource-group $ResourceGroupName --yes" "White"
        Write-Log "" "White"
        Write-Log "Cost: approximately 5-10 USD per month (much cheaper than App Service)" "Green"
        
    } else {
        Write-Log "Container deployment failed" "Red"
    }
} catch {
    Write-Log "Container deployment failed: $($_.Exception.Message)" "Red"
    Write-Log "" "White"
    Write-Log "Troubleshooting:" "Yellow"
    Write-Log "1. Check if all resource providers are registered:" "White"
    Write-Log "   az provider list --query ""[?namespace=='Microsoft.ContainerInstance']""" "White"
    Write-Log "2. Try a different region if South Africa North has issues" "White"
    Write-Log "3. Verify ACR access and image availability" "White"
    exit 1
}

Write-Log "" "White"
Write-Log "Container deployment script completed!" "Green"
