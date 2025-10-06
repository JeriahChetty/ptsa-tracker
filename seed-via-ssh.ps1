# Seed data via container SSH access

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

$CONTAINER_NAME = "ptsa-tracker-final-3018"
$RESOURCE_GROUP = "rg-ptsa-aci-za"

Write-Log "Container SSH Database Seeding" "Green"
Write-Log "=============================" "Green"

Write-Log "Opening SSH session to container..." "Yellow"
Write-Log "Once connected, run these commands:" "Cyan"
Write-Log "" "White"
Write-Log "cd /app" "White"
Write-Log "python3 comprehensive_seed.py" "White"
Write-Log "" "White"
Write-Log "Or if the file is not there:" "White"
Write-Log "python3 -c 'exec(open(\"seed_data.py\").read())'" "White"
Write-Log "" "White"

# Open SSH session
az container exec --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --exec-command "/bin/bash"
