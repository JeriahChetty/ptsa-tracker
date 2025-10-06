# Clean up unnecessary PowerShell deployment scripts

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

Write-Log "Cleaning up unnecessary PowerShell files..." "Green"
Write-Log "===========================================" "Green"

# List of files to remove (keeping only essential ones)
$filesToRemove = @(
    "check-container-status.ps1",
    "check-container-status-fixed.ps1", 
    "restart-container.ps1",
    "deploy-container-fixed-startup.ps1",
    "deploy-container-simple-python.ps1",
    "deploy-container-robust.ps1",
    "deploy-container-with-startup.ps1",
    "deploy-container-final-fixed.ps1",
    "rebuild-and-redeploy.ps1",
    "redeploy-fixed-container.ps1",
    "deploy-container-working.ps1",
    "check-app-py.ps1",
    "check-quota-usage.ps1",
    "deploy-ptsa-to-azure.ps1",
    "deploy-custom-dockerfile.ps1"
)

# Keep these essential files:
$keepFiles = @(
    "cleanup-and-deploy.ps1",
    "cleanup-ps1-files.ps1"
)

Write-Log "Files to keep:" "Yellow"
foreach ($file in $keepFiles) {
    if (Test-Path $file) {
        Write-Log "  ✅ $file" "Green"
    } else {
        Write-Log "  ❌ $file (not found)" "Red"
    }
}

Write-Log "" "White"
Write-Log "Removing unnecessary files..." "Yellow"

$removedCount = 0
foreach ($file in $filesToRemove) {
    if (Test-Path $file) {
        try {
            Remove-Item $file -Force
            Write-Log "  ✅ Removed: $file" "Green"
            $removedCount++
        } catch {
            Write-Log "  ❌ Failed to remove: $file - $_" "Red"
        }
    } else {
        Write-Log "  ⏭️ Not found: $file" "Gray"
    }
}

Write-Log "" "White"
Write-Log "Cleanup Summary:" "Cyan"
Write-Log "  Files removed: $removedCount" "White"
Write-Log "  Files kept: $($keepFiles.Count)" "White"

Write-Log "" "White"
Write-Log "Remaining PowerShell files:" "Yellow"
Get-ChildItem -Filter "*.ps1" | ForEach-Object {
    Write-Log "  📄 $($_.Name)" "White"
}

Write-Log "" "White"
Write-Log "PowerShell cleanup completed!" "Green"
Write-Log "You can now delete cleanup-ps1-files.ps1 if you want." "Gray"
