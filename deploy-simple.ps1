# Simplified Azure deployment for free tier limitations

param(
    [string]$ResourceGroupName = "rg-ptsa-simple",
    [string]$Location = "East US",
    [string]$AppName = "ptsa-simple-$(Get-Random -Maximum 9999)"
)

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

Write-Log "Starting simplified Azure deployment..." "Green"

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

# 2) Resource Group
Write-Log "Creating resource group..." "Yellow"
az group create --name $ResourceGroupName --location $Location | Out-Null

# 3) Create Web App directly with code deployment
Write-Log "Creating web app with Python runtime..." "Yellow"
try {
    # Create app service plan
    az appservice plan create `
        --name "plan-$AppName" `
        --resource-group $ResourceGroupName `
        --sku FREE `
        --is-linux 1>$null

    # Create web app
    az webapp create `
        --resource-group $ResourceGroupName `
        --plan "plan-$AppName" `
        --name $AppName `
        --runtime "PYTHON:3.11" 1>$null

    # Configure app settings
    az webapp config appsettings set `
        --resource-group $ResourceGroupName `
        --name $AppName `
        --settings `
            FLASK_ENV=production `
            FLASK_APP=app.py `
            DATABASE_URL="sqlite:///instance/ptsa.db" `
            SECRET_KEY="$(New-Guid)" `
            SCM_DO_BUILD_DURING_DEPLOYMENT=true `
            WEBSITES_ENABLE_APP_SERVICE_STORAGE=true 1>$null

    $appUrl = az webapp show --name $AppName --resource-group $ResourceGroupName --query defaultHostName --output tsv
    Write-Log ("Web app created: https://{0}" -f $appUrl) "Green"
    
    Write-Log "To deploy your code:" "Yellow"
    Write-Log "1. Initialize git: git init" "White"
    Write-Log "2. Add files: git add ." "White"
    Write-Log "3. Commit: git commit -m 'Initial commit'" "White"
    Write-Log "4. Deploy: az webapp deployment source config-local-git --resource-group $ResourceGroupName --name $AppName" "White"
    Write-Log "5. Push code: git push azure main" "White"

} catch {
    Write-Log "Failed to create web app: $_" "Red"
    exit 1
}

Write-Log "Simplified deployment completed!" "Green"
