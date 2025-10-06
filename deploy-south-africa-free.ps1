# Azure deployment script for South Africa North region with free tier options

param(
    [string]$ResourceGroupName = "rg-ptsa-tracker-za",
    [string]$Location = "South Africa North",
    [string]$AppName = "ptsa-tracker-za-$(Get-Random -Maximum 9999)",
    [string]$ACRName = "acrptsaza$(Get-Random -Maximum 999)"
)

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

Write-Log "🇿🇦 Starting Azure deployment for South Africa North (Free Tier)" "Green"
Write-Log "=================================================================" "Green"

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

# 2) Resource Group
try {
    Write-Log "Creating resource group in South Africa North..." "Yellow"
    az group create --name $ResourceGroupName --location $Location | Out-Null
    Write-Log "✅ Resource group created in South Africa North." "Green"
} catch {
    Write-Log "Failed to create resource group: $_" "Red"
    exit 1
}

# 3) Try multiple free tier options for South Africa
$planName = "asp-$AppName"
$planCreated = $false

Write-Log "Attempting App Service Plan creation with South Africa focus..." "Yellow"

# Option 1: Try Free tier in South Africa North
Write-Log "🆓 Trying Free tier (F1) in South Africa North..." "White"
try {
    $output = az appservice plan create --name $planName --resource-group $ResourceGroupName --sku F1 --location $Location 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✅ FREE TIER App Service Plan created in South Africa North!" "Green"
        $planCreated = $true
    } else {
        Write-Log "Free tier failed in South Africa North: $output" "Yellow"
    }
} catch {
    Write-Log "Free tier exception: $_" "Yellow"
}

# Option 2: Try Shared tier in South Africa North
if (-not $planCreated) {
    Write-Log "💼 Trying Shared tier (D1) in South Africa North..." "White"
    try {
        $output = az appservice plan create --name $planName --resource-group $ResourceGroupName --sku D1 --location $Location 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ SHARED TIER App Service Plan created in South Africa North!" "Green"
            $planCreated = $true
        } else {
            Write-Log "Shared tier failed in South Africa North: $output" "Yellow"
        }
    } catch {
        Write-Log "Shared tier exception: $_" "Yellow"
    }
}

# Option 3: Try Basic B1 in South Africa North (lowest paid tier)
if (-not $planCreated) {
    Write-Log "💰 Trying Basic tier (B1) in South Africa North..." "White"
    try {
        $output = az appservice plan create --name $planName --resource-group $ResourceGroupName --sku B1 --location $Location --is-linux 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ BASIC TIER App Service Plan created in South Africa North!" "Green"
            $planCreated = $true
        } else {
            Write-Log "Basic tier failed in South Africa North: $output" "Yellow"
        }
    } catch {
        Write-Log "Basic tier exception: $_" "Yellow"
    }
}

# Option 4: Try other South African regions as fallback
if (-not $planCreated) {
    $backupRegions = @("South Africa West", "West Europe", "North Europe")
    foreach ($region in $backupRegions) {
        Write-Log "🌍 Trying Free tier in backup region: $region..." "White"
        try {
            $output = az appservice plan create --name $planName --resource-group $ResourceGroupName --sku F1 --location $region 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Log "✅ App Service Plan created in $region!" "Green"
                $Location = $region  # Update location for subsequent commands
                $planCreated = $true
                break
            }
        } catch {
            Write-Log "Failed in $region" "Yellow"
        }
    }
}

if (-not $planCreated) {
    Write-Log "❌ Unable to create App Service Plan in any region" "Red"
    Write-Log "" "White"
    Write-Log "🚀 ALTERNATIVE SOLUTION: Azure Container Instances" "Cyan"
    Write-Log "Run this command instead:" "Yellow"
    Write-Log "    .\deploy-container-instances-za.ps1" "White"
    Write-Log "" "White"
    Write-Log "💡 Other options:" "Yellow"
    Write-Log "1. Request quota increase: https://portal.azure.com → Support → New support request" "White"
    Write-Log "2. Try a different Azure subscription" "White"
    Write-Log "3. Use Azure Static Web Apps for frontend only" "White"
    exit 1
}

# 4) Create Web App
Write-Log "Creating Web App..." "Yellow"
$webAppCreated = $false

try {
    Write-Log "🌐 Creating Python 3.11 web app..." "White"
    $output = az webapp create --resource-group $ResourceGroupName --plan $planName --name $AppName --runtime "PYTHON:3.11" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✅ Web App created successfully!" "Green"
        $webAppCreated = $true
    } else {
        Write-Log "Web app creation failed: $output" "Red"
        
        # Try with a different app name
        $AppName = "$AppName-alt"
        Write-Log "🔄 Trying with alternative name: $AppName" "Yellow"
        
        $output = az webapp create --resource-group $ResourceGroupName --plan $planName --name $AppName --runtime "PYTHON:3.11" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Web App created with alternative name!" "Green"
            $webAppCreated = $true
        }
    }
} catch {
    Write-Log "❌ Web App creation exception: $_" "Red"
}

if (-not $webAppCreated) {
    Write-Log "❌ Unable to create Web App" "Red"
    exit 1
}

# 5) Configure Application Settings
Write-Log "Configuring application settings..." "Yellow"

$dbConnectionString = "sqlite:///instance/ptsa.db"  # Use SQLite for free tier

try {
    az webapp config appsettings set `
        --resource-group $ResourceGroupName `
        --name $AppName `
        --settings `
            FLASK_ENV=production `
            FLASK_APP=app.py `
            DATABASE_URL="$dbConnectionString" `
            SECRET_KEY="$(New-Guid)" `
            SCM_DO_BUILD_DURING_DEPLOYMENT=true `
            WEBSITES_ENABLE_APP_SERVICE_STORAGE=true `
            'MAIL_DEFAULT_SENDER=PTSA Tracker <noreply@ptsa-tracker.com>' `
            PYTHONUNBUFFERED=1 2>$null

    if ($LASTEXITCODE -eq 0) {
        Write-Log "✅ Application settings configured" "Green"
    } else {
        Write-Log "⚠️ Some application settings may not have been applied" "Yellow"
    }
} catch {
    Write-Log "⚠️ Application settings configuration had issues: $_" "Yellow"
}

# 6) Get final URL and provide deployment info
try {
    $appUrl = az webapp show --name $AppName --resource-group $ResourceGroupName --query defaultHostName --output tsv 2>$null
    if ($appUrl) {
        Write-Log "" "White"
        Write-Log "🎉 DEPLOYMENT SUCCESSFUL!" "Green"
        Write-Log "=========================" "Green"
        Write-Log ("🌐 Your PTSA Tracker URL: https://{0}" -f $appUrl) "Cyan"
        Write-Log "📍 Region: $Location" "White"
        Write-Log "💾 Database: SQLite (local storage)" "White"
        Write-Log "" "White"
        
        Write-Log "📝 NEXT STEPS:" "Yellow"
        Write-Log "1. Deploy your code using one of these methods:" "White"
        Write-Log "   • Git deployment: az webapp deployment source config-local-git --name $AppName --resource-group $ResourceGroupName" "White"
        Write-Log "   • ZIP deployment: az webapp deployment source config-zip --src app.zip --name $AppName --resource-group $ResourceGroupName" "White"
        Write-Log "   • FTP upload to the /home/site/wwwroot directory" "White"
        Write-Log "" "White"
        
        Write-Log "🔐 DEFAULT LOGIN (once app is deployed):" "Yellow"
        Write-Log "   Email: admin@ptsa.co.za" "White"
        Write-Log "   Password: admin123" "White"
        Write-Log "   ⚠️  IMPORTANT: Change these credentials after first login!" "Red"
        Write-Log "" "White"
        
        Write-Log "🛠️ MANAGEMENT COMMANDS:" "Yellow"
        Write-Log "   View logs: az webapp log tail --name $AppName --resource-group $ResourceGroupName" "White"
        Write-Log "   Restart: az webapp restart --name $AppName --resource-group $ResourceGroupName" "White"
        Write-Log "   Scale up: az appservice plan update --name $planName --resource-group $ResourceGroupName --sku B1" "White"
        Write-Log "" "White"
        
        Write-Log "🌍 Azure Portal:" "Yellow"
        Write-Log "   https://portal.azure.com" "White"
        Write-Log "   Resource Group: $ResourceGroupName" "White"
        Write-Log "   Web App: $AppName" "White"
    } else {
        Write-Log "⚠️ Deployment completed but URL retrieval failed" "Yellow"
        Write-Log "Check Azure Portal for your app: https://portal.azure.com" "White"
    }
} catch {
    Write-Log "⚠️ Could not retrieve app URL" "Yellow"
}

Write-Log "" "White"
Write-Log "✅ South Africa deployment script completed!" "Green"
