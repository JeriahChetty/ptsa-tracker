# Final working container deployment script

param(
    [string]$ResourceGroupName = "rg-ptsa-aci-za",
    [string]$Location = "South Africa North",
    [string]$ContainerName = "ptsa-tracker-working-$(Get-Random -Maximum 9999)"
)

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

Write-Log "FINAL WORKING Azure Container Deployment" "Green"
Write-Log "=========================================" "Green"

# 1) Check login
try {
    $ctx = az account show 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Azure login required. Run: az login" }
    $ctxObj = $ctx | ConvertFrom-Json
    Write-Log ("Logged in as: {0}" -f $ctxObj.user.name) "Green"
} catch {
    Write-Log $_ "Red"
    exit 1
}

# 2) Build the fixed image
Write-Log "Building fixed Docker image..." "Yellow"
try {
    docker build -t ptsa-tracker:final .
    if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }
    Write-Log "Docker image built successfully" "Green"
} catch {
    Write-Log "Docker build failed: $_" "Red"
    exit 1
}

# 3) Test locally first
Write-Log "Testing image locally..." "Yellow"
try {
    # Stop any existing test containers
    docker stop ptsa-tracker-test 2>$null
    docker rm ptsa-tracker-test 2>$null
    
    # Run test container
    $testContainer = docker run -d --name ptsa-tracker-test -p 5001:5000 ptsa-tracker:final
    Write-Log "Started test container: $testContainer" "Green"
    
    # Wait for startup
    Start-Sleep -Seconds 30
    
    # Test the endpoint
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5001" -TimeoutSec 15 -UseBasicParsing
        Write-Log "✅ Local test successful! Status: $($response.StatusCode)" "Green"
        
        # Clean up test container
        docker stop ptsa-tracker-test 2>$null
        docker rm ptsa-tracker-test 2>$null
    } catch {
        Write-Log "❌ Local test failed: $($_.Exception.Message)" "Red"
        
        # Get container logs for debugging
        Write-Log "Getting container logs..." "Yellow"
        $logs = docker logs ptsa-tracker-test 2>&1
        Write-Log "Container logs:" "White"
        Write-Log $logs "Gray"
        
        # Clean up
        docker stop ptsa-tracker-test 2>$null
        docker rm ptsa-tracker-test 2>$null
        
        Write-Log "Local test failed. Check the logs above." "Red"
        exit 1
    }
} catch {
    Write-Log "Local testing failed: $_" "Red"
    exit 1
}

# 4) Push to ACR
Write-Log "Pushing image to ACR..." "Yellow"
try {
    az acr login --name "acrptsa298"
    docker tag ptsa-tracker:final acrptsa298.azurecr.io/ptsa-tracker:final
    docker push acrptsa298.azurecr.io/ptsa-tracker:final
    Write-Log "Image pushed to ACR successfully" "Green"
} catch {
    Write-Log "Failed to push to ACR: $_" "Red"
    exit 1
}

# 5) Create resource group
Write-Log "Creating resource group..." "Yellow"
az group create --name $ResourceGroupName --location $Location | Out-Null

# 6) Get ACR credentials
$acrLoginServer = "acrptsa298.azurecr.io"
$imageToUse = "$acrLoginServer/ptsa-tracker:final"

try {
    $acrCredsJson = az acr credential show --name "acrptsa298"
    $acrCreds = $acrCredsJson | ConvertFrom-Json
    $acrUsername = $acrCreds.username
    $passwords = $acrCreds.passwords
    $acrPassword = $passwords[0].value
    Write-Log "ACR credentials obtained" "Green"
} catch {
    Write-Log "Failed to get ACR credentials: $_" "Red"
    exit 1
}

# 7) Deploy container
Write-Log "Deploying container instance..." "Yellow"

$envVars = @(
    "FLASK_ENV=production",
    "FLASK_APP=app.py",
    "DATABASE_URL=sqlite:///app/instance/ptsa.db",
    "SECRET_KEY=ptsa-secret-$(Get-Random)",
    "PYTHONUNBUFFERED=1",
    "HOST=0.0.0.0",
    "PORT=5000"
)

try {
    az container create `
        --resource-group $ResourceGroupName `
        --name $ContainerName `
        --image $imageToUse `
        --registry-username $acrUsername `
        --registry-password $acrPassword `
        --dns-name-label $ContainerName `
        --ports 5000 `
        --cpu 1 `
        --memory 2 `
        --os-type Linux `
        --restart-policy Always `
        --environment-variables $envVars `
        --location $Location | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Log "Container created successfully!" "Green"
        
        # Wait for container to be ready
        Write-Log "Waiting 60 seconds for container startup..." "Yellow"
        Start-Sleep -Seconds 60
        
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
        
        # Get and display container logs
        Write-Log "Container startup logs:" "Yellow"
        $logs = az container logs --name $ContainerName --resource-group $ResourceGroupName 2>$null
        if ($logs) {
            Write-Log $logs "Gray"
        }
        
        Write-Log "" "White"
        
        # Test the deployed application
        if ($fqdn) {
            Write-Log "Testing deployed application..." "Yellow"
            Start-Sleep -Seconds 30  # Give it more time
            
            try {
                $response = Invoke-WebRequest -Uri "http://$fqdn`:5000" -TimeoutSec 30 -UseBasicParsing
                Write-Log "✅ DEPLOYMENT SUCCESSFUL! Application is responding" "Green"
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
                Write-Log "❌ Application not responding yet: $($_.Exception.Message)" "Red"
                Write-Log "" "White"
                Write-Log "The container is deployed but may still be starting up." "Yellow"
                Write-Log "Try accessing: http://$fqdn`:5000 in a few minutes." "Cyan"
                Write-Log "" "White"
                Write-Log "Check logs: az container logs --name $ContainerName --resource-group $ResourceGroupName" "White"
            }
        }
        
    } else {
        Write-Log "❌ Container deployment failed" "Red"
    }
} catch {
    Write-Log "Container deployment failed: $_" "Red"
    exit 1
}

Write-Log "" "White"
Write-Log "Final deployment script completed!" "Green"
