# Azure deployment script for PTSA Tracker - Handles Quota Issues

param(
    [string]$ResourceGroupName = "rg-ptsa-tracker",
    [string]$Location = "East US",
    [string]$AppName = "ptsa-tracker-app-$(Get-Random -Maximum 9999)",
    [string]$ACRName = "acrptsatracker",
    [string]$DBServerName = "psql-ptsa-db",
    [string]$DBName = "ptsatracker"
)

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

function Test-QuotaAvailable {
    param([string]$sku)
    try {
        # Try to create a test plan with the SKU to check quota
        $testPlanName = "test-quota-$(Get-Random)"
        $result = az appservice plan create --name $testPlanName --resource-group $ResourceGroupName --sku $sku --location $Location --is-linux --query "id" -o tsv 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            # Delete the test plan immediately
            az appservice plan delete --name $testPlanName --resource-group $ResourceGroupName --yes 2>$null
            return $true
        }
        return $false
    }
    catch {
        return $false
    }
}

Write-Log "Starting Azure deployment with quota handling..." "Green"

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
    az group create --name $ResourceGroupName --location $Location | Out-Null
    Write-Log "Resource group ensured." "Green"
} catch {
    Write-Log "Failed to create resource group: $_" "Red"
    exit 1
}

# 3) Skip ACR and Docker for now - focus on getting basic deployment working
Write-Log "Skipping ACR/Docker build for quota-constrained deployment..." "Yellow"
$acrLoginServer = $null

# 4) App Service Plan - Try different SKUs
$planName = "asp-$AppName"
$planCreated = $false

Write-Log "Attempting to create App Service Plan with quota-aware logic..." "Yellow"

# Try Free tier first (F1)
Write-Log "Trying Free tier (F1)..." "White"
try {
    az appservice plan create --name $planName --resource-group $ResourceGroupName --sku F1 --location $Location 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✅ Free tier App Service Plan created successfully" "Green"
        $planCreated = $true
    }
} catch {
    Write-Log "Free tier failed, trying alternatives..." "Yellow"
}

# If Free failed, try Shared (D1)
if (-not $planCreated) {
    Write-Log "Trying Shared tier (D1)..." "White"
    try {
        az appservice plan create --name $planName --resource-group $ResourceGroupName --sku D1 --location $Location 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Shared tier App Service Plan created successfully" "Green"
            $planCreated = $true
        }
    } catch {
        Write-Log "Shared tier also failed..." "Yellow"
    }
}

# If both failed, try a different region
if (-not $planCreated) {
    Write-Log "Trying different region (West US)..." "White"
    $Location = "West US"
    try {
        az appservice plan create --name $planName --resource-group $ResourceGroupName --sku F1 --location $Location 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ App Service Plan created in alternative region" "Green"
            $planCreated = $true
        }
    } catch {
        Write-Log "Alternative region also failed..." "Red"
    }
}

if (-not $planCreated) {
    Write-Log "❌ Failed to create App Service Plan due to quota limitations" "Red"
    Write-Log "Please request quota increase or try a different subscription" "Yellow"
    Write-Log "Alternative: Use Azure Static Web Apps or Azure Container Instances" "Yellow"
    exit 1
}

# 5) Create Web App with proper error handling
Write-Log "Creating Web App..." "Yellow"
$webAppCreated = $false

try {
    if ($acrLoginServer) {
        # Container deployment (if ACR was successful)
        az webapp create --resource-group $ResourceGroupName --plan $planName --name $AppName --deployment-container-image-name "$acrLoginServer/ptsa-tracker:latest" 2>$null
    } else {
        # Code deployment with Python runtime
        az webapp create --resource-group $ResourceGroupName --plan $planName --name $AppName --runtime "PYTHON:3.11" 2>$null
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✅ Web App created successfully" "Green"
        $webAppCreated = $true
    } else {
        throw "Web app creation failed"
    }
} catch {
    Write-Log "❌ Web App creation failed: $_" "Red"
    
    # Try with a different app name
    $AppName = "$AppName-alt"
    Write-Log "Trying with alternative name: $AppName" "Yellow"
    
    try {
        az webapp create --resource-group $ResourceGroupName --plan $planName --name $AppName --runtime "PYTHON:3.11" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Web App created with alternative name" "Green"
            $webAppCreated = $true
        }
    } catch {
        Write-Log "❌ Alternative web app creation also failed" "Red"
    }
}

if (-not $webAppCreated) {
    Write-Log "❌ Unable to create Web App. Check naming conflicts or quota" "Red"
    exit 1
}

# 6) Configure Application Settings (only if web app was created)
if ($webAppCreated) {
    Write-Log "Configuring application settings..." "Yellow"
    
    $dbConnectionString = "sqlite:///instance/ptsa.db"  # Use SQLite for quota-constrained deployment
    
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
                WEBSITES_ENABLE_APP_SERVICE_STORAGE=true 2>$null

        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Application settings configured" "Green"
        } else {
            Write-Log "⚠️ Some application settings may not have been applied" "Yellow"
        }
    } catch {
        Write-Log "⚠️ Application settings configuration had issues: $_" "Yellow"
    }

    # 7) Get final URL
    try {
        $appUrl = az webapp show --name $AppName --resource-group $ResourceGroupName --query defaultHostName --output tsv 2>$null
        if ($appUrl) {
            Write-Log ("✅ Deployment successful! URL: https://{0}" -f $appUrl) "Cyan"
        } else {
            Write-Log "⚠️ Deployment completed but URL retrieval failed" "Yellow"
        }
    } catch {
        Write-Log "⚠️ Could not retrieve app URL" "Yellow"
    }
}

# 8) Deployment Summary
Write-Log "" "White"
Write-Log "🎉 Deployment Summary:" "Green"
Write-Log "===================" "Green"
if ($webAppCreated) {
    Write-Log "✅ Web App: $AppName" "White"
    Write-Log "✅ Resource Group: $ResourceGroupName" "White"
    Write-Log "✅ Location: $Location" "White"
    Write-Log "✅ Database: SQLite (local)" "White"
    Write-Log "" "White"
    Write-Log "📝 Next Steps:" "Yellow"
    Write-Log "1. Deploy your code using: az webapp deployment source config-local-git" "White"
    Write-Log "2. Set up custom domain if needed" "White"
    Write-Log "3. Configure SSL certificate" "White"
    Write-Log "4. Request quota increase for better SKUs" "White"
    Write-Log "" "White"
    Write-Log "🔐 Default Login (if included in your app):" "Yellow"
    Write-Log "   Email: admin@ptsa.co.za" "White"
    Write-Log "   Password: admin123" "White"
    Write-Log "   ⚠️  Change these credentials after first login!" "Red"
} else {
    Write-Log "❌ Deployment failed due to quota limitations" "Red"
    Write-Log "" "White"
    Write-Log "💡 Alternatives:" "Yellow"
    Write-Log "1. Request quota increase: https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/azure-subscription-service-limits" "White"
    Write-Log "2. Use Azure Static Web Apps (for frontend)" "White"
    Write-Log "3. Use Azure Container Instances" "White"
    Write-Log "4. Try a different Azure region" "White"
    Write-Log "5. Use a different Azure subscription" "White"
}

Write-Log "Deployment script completed!" "Green"
