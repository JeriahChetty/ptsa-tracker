# Quick seed the live Azure app directly

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $CleanMessage = $Message -replace '[^\x00-\x7F]', ''
    
    try {
        $ValidColors = @("Black", "DarkBlue", "DarkGreen", "DarkCyan", "DarkRed", "DarkMagenta", "DarkYellow", "Gray", "DarkGray", "Blue", "Green", "Cyan", "Red", "Magenta", "Yellow", "White")
        if ($ValidColors -contains $Color) {
            Write-Host "[$ts] $CleanMessage" -ForegroundColor $Color
        } else {
            Write-Log "[$ts] $CleanMessage"
        }
    } catch {
        Write-Host "[$ts] $CleanMessage"
    }
}

Write-Log "Quick Seed Live Azure App" "Green"
Write-Log "=========================" "Green"

$APP_URL = "https://ptsa-tracker.azurewebsites.net"

# Step 1: Test if app is accessible
Write-Log "Testing app accessibility..." "Yellow"
try {
    $response = Invoke-WebRequest -Uri $APP_URL -TimeoutSec 15 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Log "✅ App is accessible" "Green"
    } else {
        Write-Log "⚠️ App responded with status: $($response.StatusCode)" "Yellow"
    }
} catch {
    Write-Log "❌ Cannot access app: $($_.Exception.Message)" "Red"
    exit 1
}

# Step 2: Test admin login endpoint
Write-Log "Testing admin login..." "Yellow"
try {
    $loginResponse = Invoke-WebRequest -Uri "$APP_URL/auth/login" -TimeoutSec 15 -UseBasicParsing
    if ($loginResponse.StatusCode -eq 200) {
        Write-Log "✅ Login page accessible" "Green"
    }
} catch {
    Write-Log "❌ Login page failed: $($_.Exception.Message)" "Red"
}

# Step 3: Manual seeding instructions
Write-Log "" "White"
Write-Log "🔧 MANUAL SEEDING STEPS:" "Cyan"
Write-Log "========================" "Cyan"
Write-Log "Since Docker isn't running, please follow these steps:" "White"
Write-Log "" "White"
Write-Log "1. Go to: $APP_URL" "Yellow"
Write-Log "2. Try logging in with existing admin credentials:" "Yellow"
Write-Log "   - admin@ptsa.co.za / admin123 (if exists)" "White"
Write-Log "   - info@ptsa.co.za / info123 (if exists)" "White"
Write-Log "" "White"
Write-Log "3. If login fails, the database is empty. We need to:" "Yellow"
Write-Log "   - Start Docker Desktop" "White"
Write-Log "   - Run the deployment script" "White"
Write-Log "" "White"

# Step 4: Check if we can run local seeding
Write-Log "Checking if we can create local admin user..." "Yellow"
try {
    # Try to run a simple Python script to create admin user
    $createAdminScript = @"
import sys
import os
sys.path.insert(0, '.')

try:
    from app import create_app
    from app.models import User, db
    from werkzeug.security import generate_password_hash
    
    # Create app with production config
    app = create_app()
    
    with app.app_context():
        # Check if admin exists
        existing_admin = User.query.filter_by(email='info@ptsa.co.za').first()
        if existing_admin:
            print("✅ Admin user already exists")
        else:
            # Create admin user
            admin = User(
                email='info@ptsa.co.za',
                password=generate_password_hash('info123'),
                role='admin',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created successfully")
            
except Exception as e:
    print(f"❌ Error: {e}")
"@

    $createAdminScript | Out-File -FilePath "temp_create_admin.py" -Encoding UTF8
    
    Write-Log "Running local admin creation..." "White"
    $result = python temp_create_admin.py
    Write-Log $result "Green"
    
    # Cleanup
    if (Test-Path "temp_create_admin.py") {
        Remove-Item "temp_create_admin.py" -Force
    }
    
} catch {
    Write-Log "Local seeding failed: $($_.Exception.Message)" "Red"
}

Write-Log "" "White"
Write-Log "📋 NEXT STEPS:" "Cyan"
Write-Log "==============" "Cyan"
Write-Log "1. Try logging in again with: info@ptsa.co.za / info123" "Yellow"
Write-Log "2. If that works, navigate to: $APP_URL/admin/seed-data" "Yellow"
Write-Log "3. Click 'Seed Database' to add all the company data" "Yellow"
Write-Log "" "White"
Write-Log "If login still fails:" "Yellow"
Write-Log "1. Start Docker Desktop" "White"
Write-Log "2. Run: .\deploy-with-updated-credentials.ps1" "White"
Write-Log "3. This will properly deploy with seeded data" "White"
