# Azure deployment script for PTSA Tracker (Fixed for subscription issues)

param(
    [string]$ResourceGroupName = "rg-ptsa-tracker",
    [string]$Location = "East US",
    [string]$AppName = "ptsa-tracker-app",
    [string]$ACRName = "acrptsatracker",
    [string]$DBServerName = "psql-ptsa-db",
    [string]$DBName = "ptsatracker"
)

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

Write-Log "Starting Azure deployment with subscription fixes..." "Green"

# 1) Login check
try {
    $ctx = az account show 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Azure login required. Run: az login" }
    $ctxObj = $ctx | ConvertFrom-Json
    Write-Log ("Logged in as: {0} (Subscription: {1})" -f $ctxObj.user.name, $ctxObj.name) "Green"
} catch {
    Write-Log $_ "Red"
    exit 1
}

# 2) Register required resource providers
Write-Log "Registering required Azure resource providers..." "Yellow"
try {
    Write-Log "Registering Microsoft.DBforPostgreSQL..." "White"
    az provider register --namespace Microsoft.DBforPostgreSQL --wait
    
    Write-Log "Registering Microsoft.Web..." "White"
    az provider register --namespace Microsoft.Web --wait
    
    Write-Log "Registering Microsoft.ContainerRegistry..." "White"
    az provider register --namespace Microsoft.ContainerRegistry --wait
    
    Write-Log "Resource providers registered successfully." "Green"
} catch {
    Write-Log "Warning: Some resource providers may not be registered. Continuing..." "Yellow"
}

# 3) Resource Group
try {
    az group create --name $ResourceGroupName --location $Location | Out-Null
    Write-Log "Resource group ensured." "Green"
} catch {
    Write-Log "Failed to create resource group: $_" "Red"
    exit 1
}

# 4) ACR (build/push locally to avoid ACR Tasks)
$acrLoginServer = $null
$acrUsername = $null
$acrPassword = $null
try {
    az acr show --name $ACRName --resource-group $ResourceGroupName 1>$null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Creating Azure Container Registry..." "White"
        az acr create --resource-group $ResourceGroupName --name $ACRName --sku Basic --admin-enabled true 1>$null
    }
    $acrLoginServer = az acr show --name $ACRName --query loginServer --output tsv
    $acrCreds = az acr credential show --name $ACRName | ConvertFrom-Json
    $acrUsername = $acrCreds.username
    $acrPassword = $acrCreds.passwords[0].value
    Write-Log "ACR ready: $acrLoginServer" "Green"

    # Docker login/build/push
    Write-Log "Building and pushing Docker image..." "White"
    $dl = docker login $acrLoginServer -u $acrUsername -p $acrPassword 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Docker login failed: $dl" }
    $db = docker build -t "$acrLoginServer/ptsa-tracker:latest" . 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Docker build failed: $db" }
    $dp = docker push "$acrLoginServer/ptsa-tracker:latest" 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Docker push failed: $dp" }
    Write-Log "Image pushed to ACR." "Green"
} catch {
    Write-Log "ACR or Docker step failed: $_" "Yellow"
    $acrLoginServer = $null
}

# 5) App Service Plan (Use B1 instead of F1 to avoid quota issues)
try {
    az appservice plan show --name "asp-$AppName" --resource-group $ResourceGroupName 1>$null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Creating App Service Plan (Basic B1)..." "White"
        az appservice plan create --name "asp-$AppName" --resource-group $ResourceGroupName --sku B1 --is-linux 1>$null
    }
    Write-Log "App Service Plan ready." "Green"
} catch {
    Write-Log "App Service Plan error: $_" "Red"
    Write-Log "Trying to create with different settings..." "Yellow"
    try {
        az appservice plan create --name "asp-$AppName" --resource-group $ResourceGroupName --sku B1 --location $Location --is-linux 1>$null
        Write-Log "App Service Plan created successfully." "Green"
    } catch {
        Write-Log "Failed to create App Service Plan. You may need to request quota increase." "Red"
        Write-Log "Skipping PostgreSQL and continuing with SQLite..." "Yellow"
    }
}

# 6) Skip PostgreSQL for now due to subscription registration issues
Write-Log "Skipping PostgreSQL due to subscription limitations. Using SQLite." "Yellow"
$dbConnectionString = "sqlite:///instance/ptsa.db"

# 7) Web App
try {
    az webapp show --name $AppName --resource-group $ResourceGroupName 1>$null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Creating Web App..." "White"
        if ($acrLoginServer) {
            az webapp create --resource-group $ResourceGroupName --plan "asp-$AppName" --name $AppName --deployment-container-image-name "$acrLoginServer/ptsa-tracker:latest" 1>$null
        } else {
            az webapp create --resource-group $ResourceGroupName --plan "asp-$AppName" --name $AppName --runtime "PYTHON:3.11" 1>$null
        }
    }
    Write-Log "Web App ready." "Green"

    if ($acrLoginServer) {
        Write-Log "Configuring container settings..." "White"
        az webapp config container set `
            --name $AppName `
            --resource-group $ResourceGroupName `
            --container-image-name "$acrLoginServer/ptsa-tracker:latest" `
            --container-registry-url "https://$acrLoginServer" `
            --container-registry-user $acrUsername `
            --container-registry-password $acrPassword 1>$null
        Write-Log "Web App container configured." "Green"
    }

    Write-Log "Configuring application settings..." "White"
    az webapp config appsettings set `
        --resource-group $ResourceGroupName `
        --name $AppName `
        --settings `
            FLASK_ENV=production `
            FLASK_APP=app.py `
            DATABASE_URL="$dbConnectionString" `
            SECRET_KEY="$(New-Guid)" `
            MAIL_SERVER="mail.ptsa.co.za" `
            MAIL_PORT=587 `
            MAIL_USE_TLS=False `
            MAIL_USE_SSL=False `
            MAIL_USERNAME="info@ptsa.co.za" `
            MAIL_PASSWORD="wqMvrJm4VZp" `
            'MAIL_DEFAULT_SENDER=ED Tracker <info@ptsa.co.za>' `
            WEBSITES_ENABLE_APP_SERVICE_STORAGE=false `
            PORT=8000 1>$null

    Write-Log "Restarting web app..." "White"
    az webapp restart --name $AppName --resource-group $ResourceGroupName 1>$null
    $appUrl = az webapp show --name $AppName --resource-group $ResourceGroupName --query defaultHostName --output tsv
    Write-Log ("Deployment complete. URL: https://{0}" -f $appUrl) "Cyan"
    
    Write-Log "Login Credentials:" "Yellow"
    Write-Log "   Admin: admin@ptsa.co.za / admin123" "White"
    Write-Log "   Change these passwords after first login!" "Red"
    
    Write-Log "" "White"
    Write-Log "Next Steps:" "Yellow"
    Write-Log "1. Register for PostgreSQL resource provider: az provider register --namespace Microsoft.DBforPostgreSQL" "White"
    Write-Log "2. Request quota increase for free tier if needed" "White"
    Write-Log "3. Consider upgrading to paid tier for better performance" "White"
    
} catch {
    Write-Log "Web App step failed: $_" "Red"
    
    Write-Log "Troubleshooting Guide:" "Yellow"
    Write-Log "1. Check your Azure subscription quota limits" "White"
    Write-Log "2. Try a different Azure region" "White"
    Write-Log "3. Register resource providers manually:" "White"
    Write-Log "   az provider register --namespace Microsoft.Web" "White"
    Write-Log "   az provider register --namespace Microsoft.DBforPostgreSQL" "White"
    Write-Log "4. Request quota increase if using free tier" "White"
    
    exit 1
}

Write-Log "Deployment script completed!" "Green"
