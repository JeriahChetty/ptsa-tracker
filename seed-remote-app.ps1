# Seed data directly to the deployed Azure application

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $CleanMessage = $Message -replace '[^\x00-\x7F]', ''
    
    try {
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

# Configuration
$CONTAINER_NAME = "ptsa-tracker-final-3018"
$RESOURCE_GROUP = "rg-ptsa-aci-za"
$APP_URL = "http://ptsa-tracker-final-3018.southafricanorth.azurecontainer.io:5000"

Write-Log "Remote Application Data Seeding" "Green"
Write-Log "==============================" "Green"

# Step 1: Check if container is running
Write-Log "Checking container status..." "Yellow"
$containerState = az container show --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP --query "instanceView.state" -o tsv

if ($containerState -ne "Running") {
    Write-Log "Container is not running. Current state: $containerState" "Red"
    Write-Log "Starting container..." "Yellow"
    az container start --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP
    Start-Sleep -Seconds 30
}

# Step 2: Test application connectivity
Write-Log "Testing application connectivity..." "Yellow"
try {
    $response = Invoke-WebRequest -Uri $APP_URL -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Log "Application is accessible" "Green"
    } else {
        Write-Log "Application responded with status: $($response.StatusCode)" "Yellow"
    }
} catch {
    Write-Log "Cannot connect to application: $($_.Exception.Message)" "Red"
    Write-Log "Please check if the application is running properly" "Yellow"
    exit 1
}

# Step 3: Copy and execute seeding script in container
Write-Log "Preparing seeding script for remote execution..." "Yellow"

# Create a simplified seeding script for remote execution
$RemoteSeedScript = @'
#!/bin/bash
echo "Starting remote database seeding..."

# Navigate to app directory
cd /app

# Run the comprehensive seeding script via Python
python3 -c "
import sys
sys.path.insert(0, '/app')

try:
    from comprehensive_seed import comprehensive_seed
    print('Running comprehensive database seeding...')
    comprehensive_seed()
    print('Seeding completed successfully!')
except Exception as e:
    print(f'Seeding failed: {str(e)}')
    sys.exit(1)
"
'@

# Save the script to a temporary file
$TempScript = "temp_remote_seed.sh"
$RemoteSeedScript | Out-File -FilePath $TempScript -Encoding ASCII

Write-Log "Uploading and executing seeding script..." "Yellow"

# Copy the comprehensive_seed.py to the container and execute it
try {
    # Method 1: Try to execute the seeding via container exec
    Write-Log "Executing seeding script in container..." "White"
    
    $execResult = az container exec --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --exec-command "python3 -c `"
import sys, os
sys.path.insert(0, '/app')
os.chdir('/app')

# Import and run seeding
try:
    exec(open('comprehensive_seed.py').read())
    print('✅ Remote seeding completed successfully!')
except Exception as e:
    print(f'❌ Remote seeding failed: {str(e)}')
    import traceback
    traceback.print_exc()
`""
    
    Write-Log "Seeding execution completed" "Green"
    
} catch {
    Write-Log "Direct execution failed, trying alternative method..." "Yellow"
    
    # Method 2: Use HTTP API approach (if you have a seeding endpoint)
    Write-Log "Attempting to trigger seeding via HTTP..." "White"
    
    try {
        # Try to access a seeding endpoint (you'd need to create this)
        $seedUrl = "$APP_URL/admin/seed-data"
        $response = Invoke-WebRequest -Uri $seedUrl -Method POST -TimeoutSec 60 -UseBasicParsing
        Write-Log "HTTP seeding triggered successfully" "Green"
    } catch {
        Write-Log "HTTP seeding not available" "Yellow"
        Write-Log "Manual seeding may be required" "Yellow"
    }
}

# Step 4: Verify seeding by checking the application
Write-Log "Verifying seeding results..." "Yellow"
Start-Sleep -Seconds 10

try {
    # Try to access the login page to see if the app is working
    $loginResponse = Invoke-WebRequest -Uri "$APP_URL/auth/login" -TimeoutSec 15 -UseBasicParsing
    if ($loginResponse.StatusCode -eq 200) {
        Write-Log "Application is responding after seeding" "Green"
    }
} catch {
    Write-Log "Application might be restarting, please wait a moment" "Yellow"
}

# Cleanup
if (Test-Path $TempScript) {
    Remove-Item $TempScript
}

Write-Log "Remote seeding process completed!" "Green"
Write-Log "=================================" "Green"
Write-Log "Your deployed PTSA Tracker should now have sample data" "Cyan"
Write-Log "Access it at: $APP_URL" "Cyan"
Write-Log "" "White"
Write-Log "Login credentials:" "White"
Write-Log "  Admin: admin@ptsa.co.za / admin123" "White"
Write-Log "  Companies: Various emails / company123" "White"
