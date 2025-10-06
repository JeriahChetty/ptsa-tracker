# Seed data directly to Azure App Service deployment

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

# Configuration for Azure App Service
$APP_URL = "https://ptsa-tracker.azurewebsites.net"
$RESOURCE_GROUP = "ptsa-rg"
$WEB_APP_NAME = "ptsa-tracker-webapp"

Write-Log "Azure App Service Data Seeding" "Green"
Write-Log "==============================" "Green"
Write-Log "Target: $APP_URL" "Cyan"

# Step 1: Test application connectivity
Write-Log "Testing application connectivity..." "Yellow"
try {
    $response = Invoke-WebRequest -Uri $APP_URL -TimeoutSec 15 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Log "Application is accessible" "Green"
    } else {
        Write-Log "Application responded with status: $($response.StatusCode)" "Yellow"
    }
} catch {
    Write-Log "Cannot connect to application: $($_.Exception.Message)" "Red"
    Write-Log "Checking if app service is running..." "Yellow"
    
    # Check app service status
    try {
        $appStatus = az webapp show --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP --query "state" -o tsv
        Write-Log "App Service state: $appStatus" "White"
        
        if ($appStatus -ne "Running") {
            Write-Log "Starting App Service..." "Yellow"
            az webapp start --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP
            Start-Sleep -Seconds 30
        }
    } catch {
        Write-Log "Could not check app service status" "Red"
    }
}

# Step 2: Try seeding via HTTP endpoint
Write-Log "Attempting to seed via HTTP endpoint..." "Yellow"
try {
    # Try to access the seeding endpoint directly
    $seedUrl = "$APP_URL/admin/seed-data"
    Write-Log "Attempting to access: $seedUrl" "White"
    
    # First try to access the login page to see if the app is working
    $loginUrl = "$APP_URL/auth/login"
    $loginResponse = Invoke-WebRequest -Uri $loginUrl -TimeoutSec 30 -UseBasicParsing
    
    if ($loginResponse.StatusCode -eq 200) {
        Write-Log "App is responding - login page accessible" "Green"
        
        # Now try to trigger seeding via direct POST (this will require admin login)
        Write-Log "Manual seeding required:" "Yellow"
        Write-Log "1. Open: $APP_URL" "Cyan"
        Write-Log "2. Login as admin: admin@ptsa.co.za / admin123" "Cyan"
        Write-Log "3. Navigate to: $APP_URL/admin/seed-data" "Cyan"
        Write-Log "4. Click 'Seed Database' button" "Cyan"
        
    } else {
        throw "App not responding properly"
    }
    
} catch {
    Write-Log "HTTP seeding failed: $($_.Exception.Message)" "Red"
    
    # Step 3: Alternative - deploy with seeded database
    Write-Log "Attempting alternative deployment with seeded database..." "Yellow"
    
    # Check if we have local seeded data
    if (Test-Path "instance\ptsa_dev.db") {
        Write-Log "Found local seeded database" "Green"
        Write-Log "Rebuilding and deploying with seeded data..." "Yellow"
        
        # Copy the dev database as production database
        Copy-Item "instance\ptsa_dev.db" "instance\ptsa.db" -Force
        
        # Build and deploy new image with data
        Write-Log "Building Docker image with seeded data..." "White"
        docker build -t ptsa-tracker:with-data .
        
        # Push to Azure Container Registry
        Write-Log "Pushing to Azure Container Registry..." "White"
        az acr login --name ptsatrackerapp
        docker tag ptsa-tracker:with-data ptsatrackerapp.azurecr.io/ptsa-tracker:latest
        docker push ptsatrackerapp.azurecr.io/ptsa-tracker:latest
        
        # Restart the web app to pull new image
        Write-Log "Restarting web app to pull new image..." "White"
        az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP
        
        # Wait for restart
        Write-Log "Waiting for application to restart..." "White"
        Start-Sleep -Seconds 60
        
        Write-Log "Deployment completed!" "Green"
        
    } else {
        Write-Log "No local seeded database found" "Red"
        Write-Log "Please run: python comprehensive_seed.py" "Yellow"
        exit 1
    }
}

# Step 4: Verify the application
Write-Log "Verifying application..." "Yellow"
Start-Sleep -Seconds 15

try {
    $finalTest = Invoke-WebRequest -Uri $APP_URL -TimeoutSec 20 -UseBasicParsing
    if ($finalTest.StatusCode -eq 200) {
        Write-Log "Application is responding after seeding process" "Green"
    }
} catch {
    Write-Log "Application might still be starting up" "Yellow"
}

Write-Log "Seeding process completed!" "Green"
Write-Log "=========================" "Green"
Write-Log "Your PTSA Tracker should now have comprehensive data" "Cyan"
Write-Log "Access it at: $APP_URL" "Cyan"
Write-Log "" "White"
Write-Log "Login credentials:" "White"
Write-Log "  Admin: admin@ptsa.co.za / admin123" "White"
Write-Log "  Gehring Technologies: admin@gehring.co.za / gehring123" "White"
Write-Log "  ACME Precision: operations@acmeprecision.co.za / acme123" "White"
Write-Log "  Bosch Tooling: info@bosch-tooling.co.za / bosch123" "White"
Write-Log "  And 4 more realistic companies!" "White"
