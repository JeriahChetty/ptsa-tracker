# Script to copy local database to the cloud container

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

Write-Log "🗄️ Copy Local Database to Cloud Container" "Green"
Write-Log "===========================================" "Green"

# Configuration
$CONTAINER_NAME = "ptsa-tracker-final-2625"
$RESOURCE_GROUP = "rg-ptsa-aci-za"
$LOCAL_DB_PATH = "instance\ptsa_dev.db"
$REMOTE_DB_PATH = "/app/instance/ptsa.db"

# Step 1: Check if local database exists
if (-not (Test-Path $LOCAL_DB_PATH)) {
    Write-Log "❌ Local database not found at: $LOCAL_DB_PATH" "Red"
    Write-Log "💡 Make sure you've run seed_data.py first" "Yellow"
    exit 1
}

Write-Log "✅ Found local database: $LOCAL_DB_PATH" "Green"

# Step 2: Stop the container temporarily
Write-Log "⏸️  Stopping container for database update..." "Yellow"
az container stop --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP

# Wait for container to stop
Write-Log "⏳ Waiting for container to stop..." "Yellow"
Start-Sleep -Seconds 30

# Step 3: Create a backup of current database in container
Write-Log "📋 Creating backup of current cloud database..." "Yellow"
try {
    az container exec --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --exec-command "cp /app/instance/ptsa.db /app/instance/ptsa_backup.db"
    Write-Log "✅ Backup created" "Green"
} catch {
    Write-Log "⚠️  Could not create backup (container might be empty)" "Yellow"
}

# Step 4: Copy local database to container using az container exec
Write-Log "📤 Copying local database to cloud container..." "Yellow"

# Convert the database to base64 for transfer
$base64Content = [Convert]::ToBase64String([IO.File]::ReadAllBytes($LOCAL_DB_PATH))
$tempFile = "temp_db_transfer.txt"
$base64Content | Out-File -FilePath $tempFile -Encoding ascii

Write-Log "📁 Database converted to base64 for transfer" "White"

# Transfer the base64 content and decode it in the container
$transferCommand = @"
echo '$base64Content' | base64 -d > $REMOTE_DB_PATH && echo 'Database transfer completed successfully'
"@

# Save the command to a temporary file
$transferCommand | Out-File -FilePath "transfer_command.sh" -Encoding ascii -NoNewline

# Execute the transfer
try {
    az container exec --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --exec-command "bash -c `"echo '$base64Content' | base64 -d > $REMOTE_DB_PATH`""
    Write-Log "✅ Database copied successfully" "Green"
} catch {
    Write-Log "❌ Database copy failed, trying alternative method..." "Red"
    
    # Alternative: Use file upload if available
    Write-Log "🔄 Trying alternative copy method..." "Yellow"
    # This would require Azure File Share or other method
    Write-Log "⚠️  Manual copy required. Please upload $LOCAL_DB_PATH to the container" "Yellow"
}

# Step 5: Verify the database was copied
Write-Log "🔍 Verifying database copy..." "Yellow"
try {
    $verification = az container exec --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --exec-command "ls -la /app/instance/"
    if ($verification -match "ptsa.db") {
        Write-Log "✅ Database file exists in container" "Green"
    } else {
        Write-Log "❌ Database file not found in container" "Red"
    }
} catch {
    Write-Log "⚠️  Could not verify database copy" "Yellow"
}

# Step 6: Restart the container
Write-Log "🔄 Restarting container..." "Yellow"
az container restart --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP

# Step 7: Wait for restart and test
Write-Log "⏳ Waiting for container to restart..." "Yellow"
Start-Sleep -Seconds 45

Write-Log "🧪 Testing application..." "Yellow"
$testUrl = "http://ptsa-tracker-final-2625.southafricanorth.azurecontainer.io:5000"
try {
    $response = Invoke-WebRequest -Uri $testUrl -TimeoutSec 15 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Log "✅ Application is responding!" "Green"
        Write-Log "🌐 Your PTSA Tracker with local data is now available at:" "Green"
        Write-Log "   $testUrl" "Cyan"
    } else {
        Write-Log "⚠️  Application responded with status: $($response.StatusCode)" "Yellow"
    }
} catch {
    Write-Log "❌ Application test failed: $($_.Exception.Message)" "Red"
    Write-Log "💡 Check the container logs:" "Yellow"
    Write-Log "   az container logs --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP" "White"
}

# Cleanup temp files
if (Test-Path $tempFile) { Remove-Item $tempFile }
if (Test-Path "transfer_command.sh") { Remove-Item "transfer_command.sh" }

Write-Log "🎉 Database copy operation completed!" "Green"
Write-Log "================================" "Green"
Write-Log "🔐 Your login credentials remain:" "White"
Write-Log "   Admin: admin@ptsa.co.za / admin123" "White"
Write-Log "   Companies: Use the credentials from your local seeding" "White"
