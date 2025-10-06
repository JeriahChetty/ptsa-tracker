# Alternative deployment using Azure Container Instances for South Africa

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

# 2) Create resource group
Write-Log "Creating resource group in South Africa North..." "Yellow"
az group create --name $ResourceGroupName --location $Location | Out-Null

# 3) Create Azure Container Registry
Write-Log "Creating Azure Container Registry..." "Yellow"
try {
    az acr create --resource-group $ResourceGroupName --name $ACRName --sku Basic --admin-enabled true | Out-Null
    $acrLoginServer = az acr show --name $ACRName --query loginServer --output tsv
    Write-Log "ACR created: $acrLoginServer" "Green"
} catch {
    Write-Log "Failed to create ACR. Trying to use existing or public image..." "Yellow"
    $acrLoginServer = $null
}

# 4) Build and push image (if ACR available)
$imageToUse = "python:3.11-slim"  # Fallback to public image

if ($acrLoginServer) {
    Write-Log "Building and pushing image to ACR..." "Yellow"
    try {
        # Login to ACR
        az acr login --name $ACRName 2>$null
        
        # Build and push
        docker build -t "$acrLoginServer/ptsa-tracker:latest" . 2>$null
        if ($LASTEXITCODE -eq 0) {
            docker push "$acrLoginServer/ptsa-tracker:latest" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $imageToUse = "$acrLoginServer/ptsa-tracker:latest"
                Write-Log "Custom image built and pushed" "Green"
            }
        }
    } catch {
        Write-Log "Custom image build failed, using fallback" "Yellow"
    }
}

# 5) Deploy container instance
Write-Log "Deploying container instance..." "Yellow"

$envVars = @(
    "FLASK_ENV=production",
    "FLASK_APP=app.py",
    "DATABASE_URL=sqlite:///tmp/ptsa.db",
    "SECRET_KEY=ptsa-secret-$(Get-Random)"
)

try {
    if ($acrLoginServer -and $imageToUse.Contains($acrLoginServer)) {
        # Use ACR image with credentials
        $acrUsername = az acr credential show --name $ACRName --query username --output tsv
        $acrPassword = az acr credential show --name $ACRName --query "passwords[0].value" --output tsv
        
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
            --environment-variables $envVars `
            --location $Location | Out-Null
    } else {
        # Use public image - create a simple Flask container
        Write-Log "Creating simple container with public image..." "White"
        
        az container create `
            --resource-group $ResourceGroupName `
            --name $ContainerName `
            --image "nginx:alpine" `
            --dns-name-label $ContainerName `
            --ports 80 `
            --cpu 0.5 `
            --memory 0.5 `
            --location $Location | Out-Null
    }

    if ($LASTEXITCODE -eq 0) {
        # Get the FQDN
        $fqdn = az container show --resource-group $ResourceGroupName --name $ContainerName --query ipAddress.fqdn --output tsv
        $port = if ($imageToUse.Contains("nginx")) { "80" } else { "5000" }
        
        Write-Log "" "White"
        Write-Log "CONTAINER DEPLOYMENT SUCCESSFUL!" "Green"
        Write-Log "===================================" "Green"
        Write-Log "URL: http://$fqdn`:$port" "Cyan"
        Write-Log "Region: $Location" "White"
        Write-Log "Container: $ContainerName" "White"
        Write-Log "" "White"
        
        if ($imageToUse.Contains("nginx")) {
            Write-Log "This is a placeholder container (nginx)" "Yellow"
            Write-Log "To deploy your Flask app:" "Yellow"
            Write-Log "1. Fix the Dockerfile and ACR issues" "White"
            Write-Log "2. Re-run this script" "White"
            Write-Log "3. Or manually update the container image" "White"
        } else {
            Write-Log "Default login:" "Yellow"
            Write-Log "   Email: admin@ptsa.co.za" "White"
            Write-Log "   Password: admin123" "White"
        }
        
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
    Write-Log "Container deployment failed: $_" "Red"
}

Write-Log "" "White"
Write-Log "Container deployment script completed!" "Green"
