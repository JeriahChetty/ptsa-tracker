# Script to check container health and diagnose issues

param(
    [string]$ContainerName = "ptsa-tracker-robust-*",
    [string]$ResourceGroupName = "rg-ptsa-aci-za"
)

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

Write-Log "Container Health Check" "Green"
Write-Log "=====================" "Green"

# Find containers matching the pattern
if ($ContainerName.Contains("*")) {
    $containers = az container list --resource-group $ResourceGroupName --query "[?contains(name, 'ptsa-tracker')].name" --output tsv
    if ($containers) {
        $ContainerName = ($containers -split "`n")[0]
        Write-Log "Found container: $ContainerName" "Green"
    } else {
        Write-Log "No containers found matching pattern" "Red"
        exit 1
    }
}

# 1) Container Status
Write-Log "1. Container Status:" "Yellow"
$status = az container show --name $ContainerName --resource-group $ResourceGroupName --query "{name:name,state:instanceView.state,restartCount:instanceView.restartCount,provisioningState:provisioningState}" --output table
Write-Log $status "White"

# 2) Container Events
Write-Log "`n2. Container Events:" "Yellow"
$events = az container show --name $ContainerName --resource-group $ResourceGroupName --query "instanceView.events" --output table
if ($events) {
    Write-Log $events "White"
} else {
    Write-Log "No events found" "Gray"
}

# 3) Container Logs
Write-Log "`n3. Container Logs:" "Yellow"
$logs = az container logs --name $ContainerName --resource-group $ResourceGroupName 2>$null
if ($logs) {
    Write-Log $logs "Gray"
} else {
    Write-Log "No logs available" "Yellow"
}

# 4) Network Configuration
Write-Log "`n4. Network Configuration:" "Yellow"
$network = az container show --name $ContainerName --resource-group $ResourceGroupName --query "{fqdn:ipAddress.fqdn,ip:ipAddress.ip,ports:ipAddress.ports}" --output table
Write-Log $network "White"

# 5) Environment Variables
Write-Log "`n5. Environment Variables:" "Yellow"
$env = az container show --name $ContainerName --resource-group $ResourceGroupName --query "containers[0].environmentVariables[?name!='SECRET_KEY' && name!='MAIL_PASSWORD']" --output table
Write-Log $env "White"

# 6) Test connectivity
Write-Log "`n6. Testing Connectivity:" "Yellow"
$fqdn = az container show --name $ContainerName --resource-group $ResourceGroupName --query ipAddress.fqdn --output tsv
if ($fqdn) {
    Write-Log "Testing: http://$fqdn`:5000" "White"
    try {
        $response = Invoke-WebRequest -Uri "http://$fqdn`:5000" -TimeoutSec 10 -UseBasicParsing
        Write-Log "✅ SUCCESS: HTTP $($response.StatusCode)" "Green"
    } catch {
        Write-Log "❌ FAILED: $($_.Exception.Message)" "Red"
        
        # Try to get more details
        Write-Log "Getting detailed error..." "Yellow"
        try {
            $detailedError = Invoke-WebRequest -Uri "http://$fqdn`:5000" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        } catch {
            $errorDetails = $_.Exception
            Write-Log "Error Type: $($errorDetails.GetType().Name)" "Red"
            Write-Log "Error Message: $($errorDetails.Message)" "Red"
            if ($errorDetails.InnerException) {
                Write-Log "Inner Exception: $($errorDetails.InnerException.Message)" "Red"
            }
        }
    }
} else {
    Write-Log "No FQDN available" "Red"
}

Write-Log "`nHealth check completed!" "Green"
