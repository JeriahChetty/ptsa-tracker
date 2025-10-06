# Test if we can run comprehensive seeding on the Azure app

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

$APP_URL = "https://ptsa-tracker.azurewebsites.net"

Write-Log "Testing Azure App Service Seeding" "Green"
Write-Log "=================================" "Green"

# Test 1: Check if app is responding
Write-Log "Testing basic connectivity..." "Yellow"
try {
    $response = Invoke-WebRequest -Uri $APP_URL -TimeoutSec 15 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Log "App is responding - Status: $($response.StatusCode)" "Green"
    } else {
        Write-Log "App responded with status: $($response.StatusCode)" "Yellow"
    }
} catch {
    Write-Log "App connectivity failed: $($_.Exception.Message)" "Red"
    exit 1
}

# Test 2: Try to access the admin login
Write-Log "Testing admin login page..." "Yellow"
try {
    $loginResponse = Invoke-WebRequest -Uri "$APP_URL/auth/login" -TimeoutSec 15 -UseBasicParsing
    if ($loginResponse.StatusCode -eq 200) {
        Write-Log "Login page accessible" "Green"
    } else {
        Write-Log "Login page status: $($loginResponse.StatusCode)" "Yellow"
    }
} catch {
    Write-Log "Login page failed: $($_.Exception.Message)" "Red"
}

# Test 3: Try to access the seeding endpoint (should redirect to login)
Write-Log "Testing seeding endpoint..." "Yellow"
try {
    $seedResponse = Invoke-WebRequest -Uri "$APP_URL/admin/seed-data" -TimeoutSec 15 -UseBasicParsing -MaximumRedirection 0 -ErrorAction SilentlyContinue
    Write-Log "Seed endpoint status: $($seedResponse.StatusCode)" "White"
} catch {
    if ($_.Exception.Response.StatusCode -eq 302) {
        Write-Log "Seed endpoint exists (redirects to login as expected)" "Green"
    } else {
        Write-Log "Seed endpoint error: $($_.Exception.Message)" "Yellow"
    }
}

Write-Log "Next steps:" "Cyan"
Write-Log "1. Access: $APP_URL" "White"
Write-Log "2. Login as: admin@ptsa.co.za / admin123" "White"
Write-Log "3. Navigate to: $APP_URL/admin/seed-data" "White"
Write-Log "4. Click 'Seed Database' button" "White"
