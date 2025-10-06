# Register all Azure resource providers needed for PTSA Tracker

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message" -ForegroundColor $Color
}

Write-Log "Registering Azure Resource Providers for PTSA Tracker" "Green"
Write-Log "====================================================" "Green"

# Check login
try {
    $ctx = az account show 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Azure login required. Run: az login" }
    $ctxObj = $ctx | ConvertFrom-Json
    Write-Log ("Logged in as: {0}" -f $ctxObj.user.name) "Green"
} catch {
    Write-Log $_ "Red"
    exit 1
}

# List of required providers
$providers = @(
    "Microsoft.Web",
    "Microsoft.ContainerInstance", 
    "Microsoft.ContainerRegistry",
    "Microsoft.DBforPostgreSQL",
    "Microsoft.Storage",
    "Microsoft.Insights"
)

Write-Log "Registering resource providers..." "Yellow"

foreach ($provider in $providers) {
    try {
        Write-Log "Registering $provider..." "White"
        az provider register --namespace $provider --wait
        
        # Check registration status
        $status = az provider show --namespace $provider --query "registrationState" -o tsv
        if ($status -eq "Registered") {
            Write-Log "✅ $provider registered successfully" "Green"
        } else {
            Write-Log "⚠️ $provider status: $status" "Yellow"
        }
    } catch {
        Write-Log "❌ Failed to register $provider" "Red"
    }
}

Write-Log "" "White"
Write-Log "Provider registration complete!" "Green"
Write-Log "You can now run the container deployment script:" "Yellow"
Write-Log "    .\deploy-container-final.ps1" "Cyan"
