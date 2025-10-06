# Azure Static Web Apps deployment for South Africa (completely free option)

param(
    [string]$ResourceGroupName = "rg-ptsa-swa-za",
    [string]$Location = "South Africa North",
    [string]$SwaName = "ptsa-tracker-swa-$(Get-Random -Maximum 9999)"
)

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

Write-Log "🆓 Azure Static Web Apps deployment (100% FREE)" "Green"
Write-Log "===============================================" "Green"

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

# 3) Check if SWA extension is installed
Write-Log "Checking Azure CLI extensions..." "Yellow"
$swaExtension = az extension list --query "[?name=='staticwebapp'].name" -o tsv

if (-not $swaExtension) {
    Write-Log "Installing Static Web Apps extension..." "White"
    az extension add --name staticwebapp | Out-Null
    Write-Log "✅ Extension installed" "Green"
} else {
    Write-Log "✅ Static Web Apps extension already installed" "Green"
}

# 4) Create Static Web App
Write-Log "Creating Static Web App..." "Yellow"

try {
    # Note: Static Web Apps are only available in certain regions
    # We'll use the global region but mention South Africa support
    $output = az staticwebapp create `
        --name $SwaName `
        --resource-group $ResourceGroupName `
        --location "Central US" `
        --source https://github.com/your-username/ptsa-tracker `
        --branch main `
        --app-location "/" `
        --api-location "api" `
        --output-location "dist" 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Log "✅ Static Web App created!" "Green"
        
        # Get the URL
        $swaUrl = az staticwebapp show --name $SwaName --resource-group $ResourceGroupName --query defaultHostname --output tsv
        
        Write-Log "" "White"
        Write-Log "🎉 STATIC WEB APP DEPLOYMENT SUCCESSFUL!" "Green"
        Write-Log "=========================================" "Green"
        Write-Log "🌐 URL: https://$swaUrl" "Cyan"
        Write-Log "🆓 Cost: FREE (no charges)" "Green"
        Write-Log "📍 CDN: Global with South Africa edge locations" "White"
        Write-Log "" "White"
        
        Write-Log "📝 NEXT STEPS:" "Yellow"
        Write-Log "1. Push your code to GitHub repository" "White"
        Write-Log "2. Configure GitHub Actions for deployment" "White"
        Write-Log "3. Add API functions for backend functionality" "White"
        Write-Log "" "White"
        
        Write-Log "ℹ️  LIMITATIONS OF STATIC WEB APPS:" "Yellow"
        Write-Log "• Frontend only (HTML, CSS, JS)" "White"
        Write-Log "• Backend requires Azure Functions" "White"
        Write-Log "• No direct Flask support" "White"
        Write-Log "• Best for React/Vue/Angular apps" "White"
        Write-Log "" "White"
        
        Write-Log "💡 RECOMMENDATION:" "Cyan"
        Write-Log "For your Flask app, try the Container Instances option:" "White"
        Write-Log "    .\deploy-container-instances-za.ps1" "Green"
        
    } else {
        Write-Log "❌ Static Web App creation failed: $output" "Red"
        Write-Log "" "White"
        Write-Log "This might be because:" "Yellow"
        Write-Log "• GitHub repository URL is not accessible" "White"
        Write-Log "• Static Web Apps quota exceeded" "White"
        Write-Log "• Region not supported" "White"
    }
    
} catch {
    Write-Log "❌ Static Web App creation failed: $_" "Red"
}

Write-Log "" "White"
Write-Log "✅ Static Web App script completed!" "Green"
