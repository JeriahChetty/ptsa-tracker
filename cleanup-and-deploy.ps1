# Clean up old containers and deploy new one due to quota limits

param(
    [string]$ResourceGroupName = "rg-ptsa-aci-za",
    [string]$Location = "South Africa North",
    [string]$ContainerName = "ptsa-tracker-final-$(Get-Random -Maximum 9999)"
)

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    # Clean message of problematic characters
    $CleanMessage = $Message -replace '[^\x00-\x7F]', ''
    
    try {
        # Validate color parameter
        $ValidColors = @("Black", "DarkBlue", "DarkGreen", "DarkCyan", "DarkRed", "DarkMagenta", "DarkYellow", "Gray", "DarkGray", "Blue", "Green", "Cyan", "Red", "Magenta", "Yellow", "White")
        if ($ValidColors -contains $Color) {
            Write-Host "[$ts] $CleanMessage" -ForegroundColor $Color
        } else {
            Write-Host "[$ts] $CleanMessage"
        }
    } catch {
        Write-Host "[$ts] $CleanMessage"
    }
}

Write-Log "PTSA Tracker - Clean up and Deploy" "Green"
Write-Log "==================================" "Green"

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

# 2) List existing containers in the resource group
Write-Log "Checking existing containers..." "Yellow"
try {
    $containerListJson = az container list --resource-group $ResourceGroupName --output json 2>$null
    if ($containerListJson) {
        $containers = $containerListJson | ConvertFrom-Json
        Write-Log "Found $($containers.Count) existing container(s)" "White"
        
        foreach ($container in $containers) {
            Write-Log "  - $($container.name) (Status: $($container.instanceView.state))" "White"
        }
    } else {
        Write-Log "No existing containers found" "White"
        $containers = @()
    }
} catch {
    Write-Log "Could not list containers, assuming none exist" "Yellow"
    $containers = @()
}

# 3) Clean up old containers
if ($containers.Count -gt 0) {
    Write-Log "Cleaning up old containers to free quota..." "Yellow"
    
    foreach ($container in $containers) {
        try {
            Write-Log "Deleting container: $($container.name)" "White"
            az container delete --name $container.name --resource-group $ResourceGroupName --yes | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                Write-Log "✅ Deleted: $($container.name)" "Green"
            } else {
                Write-Log "⚠️ Failed to delete: $($container.name)" "Yellow"
            }
        } catch {
            Write-Log "⚠️ Error deleting $($container.name): $_" "Yellow"
        }
    }
    
    # Wait for cleanup to complete
    Write-Log "Waiting 30 seconds for cleanup to complete..." "Yellow"
    Start-Sleep -Seconds 30
} else {
    Write-Log "No containers to clean up" "Green"
}

# 4) Use existing ACR
$acrLoginServer = "acrptsa298.azurecr.io"
$imageToUse = "$acrLoginServer/ptsa-tracker:latest"

try {
    Write-Log "Getting ACR credentials..." "Yellow"
    $acrCredsJson = az acr credential show --name "acrptsa298"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to retrieve ACR credentials"
    }
    
    $acrCreds = $acrCredsJson | ConvertFrom-Json
    $acrUsername = $acrCreds.username
    $passwords = $acrCreds.passwords
    $acrPassword = $passwords[0].value
    
    Write-Log "ACR credentials obtained" "Green"
} catch {
    Write-Log "Failed to get ACR credentials: $_" "Red"
    exit 1
}

# 5) Deploy new container with fixed configuration
Write-Log "Deploying new container..." "Yellow"

$envVars = @(
    "FLASK_ENV=production",
    "FLASK_APP=app.py",
    "DATABASE_URL=sqlite:////app/instance/ptsa.db",
    "SECRET_KEY=ptsa-secret-$(Get-Random)",
    "PYTHONUNBUFFERED=1",
    "HOST=0.0.0.0",
    "PORT=5000"
)

try {
    Write-Log "Creating container: $ContainerName" "White"
    
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
        --location $Location | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Log "Container created successfully!" "Green"
        
        # Get container details
        $fqdn = az container show --resource-group $ResourceGroupName --name $ContainerName --query ipAddress.fqdn --output tsv
        $state = az container show --resource-group $ResourceGroupName --name $ContainerName --query instanceView.state --output tsv
        
        Write-Log "" "White"
        Write-Log "🎉 DEPLOYMENT SUCCESSFUL!" "Green"
        Write-Log "=========================" "Green"
        Write-Log "Container State: $state" "White"
        Write-Log "URL: http://$fqdn`:5000" "Cyan"
        Write-Log "Container: $ContainerName" "White"
        Write-Log "" "White"
        
        # Wait and test
        Write-Log "Waiting 90 seconds for container startup..." "Yellow"
        Start-Sleep -Seconds 90
        
        # Get container logs
        Write-Log "Getting container logs..." "White"
        $logs = az container logs --name $ContainerName --resource-group $ResourceGroupName 2>$null
        if ($logs) {
            Write-Log "Container startup logs:" "Green"
            Write-Log $logs "Gray"
        } else {
            Write-Log "No logs available yet" "Yellow"
        }
        
        Write-Log "" "White"
        
        # Test the application
        Write-Log "Testing deployed application..." "Yellow"
        try {
            $response = Invoke-WebRequest -Uri "http://$fqdn`:5000" -TimeoutSec 30 -UseBasicParsing
            Write-Log "✅ SUCCESS! Application is responding" "Green"
            Write-Log "Status Code: $($response.StatusCode)" "Green"
            
            Write-Log "" "White"
            Write-Log "🎉 PTSA Tracker is now running at:" "Green"
            Write-Log "   http://$fqdn`:5000" "Cyan"
            Write-Log "" "White"
            Write-Log "Default Login:" "Yellow"
            Write-Log "   Email: admin@ptsa.co.za" "White"
            Write-Log "   Password: admin123" "White"
            Write-Log "   ⚠️ IMPORTANT: Change these credentials after first login!" "Red"
            
        } catch {
            Write-Log "❌ Application not responding: $($_.Exception.Message)" "Red"
            Write-Log "" "White"
            Write-Log "Troubleshooting:" "Yellow"
            Write-Log "1. Container may still be starting - wait a few more minutes" "White"
            Write-Log "2. Check logs: az container logs --name $ContainerName --resource-group $ResourceGroupName" "White"
            Write-Log "3. Check container status: az container show --name $ContainerName --resource-group $ResourceGroupName" "White"
            Write-Log "" "White"
            Write-Log "Try accessing: http://$fqdn`:5000 in your browser" "Cyan"
        }
        
    } else {
        Write-Log "❌ Container deployment failed" "Red"
        Write-Log "This might be due to quota limits or other Azure issues" "Yellow"
        
        # Show quota status
        Write-Log "" "White"
        Write-Log "Checking quota usage..." "Yellow"
        try {
            $quotaInfo = az vm list-usage --location "$Location" --query "[?localName=='Standard Cores']" --output table 2>$null
            if ($quotaInfo) {
                Write-Log $quotaInfo "White"
            }
        } catch {
            Write-Log "Could not retrieve quota information" "Yellow"
        }
    }
} catch {
    Write-Log "Container deployment failed: $_" "Red"
}

Write-Log "" "White"
Write-Log "Management Commands:" "Yellow"
Write-Log "   View logs: az container logs --name $ContainerName --resource-group $ResourceGroupName" "White"
Write-Log "   Restart: az container restart --name $ContainerName --resource-group $ResourceGroupName" "White"
Write-Log "   Delete: az container delete --name $ContainerName --resource-group $ResourceGroupName --yes" "White"

Write-Log "" "White"
Write-Log "Cleanup and deployment script completed!" "Green"
