# PowerShell script for running Docker containers on Windows
param(
    [string]$Command = "start",
    [string]$Mode = "production",
    [switch]$Foreground,
    [switch]$Build,
    [switch]$Help
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"

function Write-Log {
    param([string]$Message, [string]$Color = $Blue)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Write-Error-Log {
    param([string]$Message)
    Write-Log "ERROR: $Message" $Red
}

function Write-Success {
    param([string]$Message)
    Write-Log "SUCCESS: $Message" $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Log "WARNING: $Message" $Yellow
}

function Show-Help {
    Write-Host @"
Usage: .\run.ps1 [OPTIONS] [COMMAND]

Run Telegram Promo Bot in Docker container

COMMANDS:
    start       Start the bot (default)
    stop        Stop the bot
    restart     Restart the bot
    logs        Show bot logs
    status      Show container status
    build       Build and run the bot

OPTIONS:
    -Mode MODE          Run mode: production (default) or development
    -Foreground         Run in foreground (don't detach)
    -Build              Build image before running
    -Help               Show this help message

EXAMPLES:
    .\run.ps1                       # Start bot in production mode
    .\run.ps1 -Mode development     # Start bot in development mode
    .\run.ps1 stop                  # Stop the bot
    .\run.ps1 logs                  # Show logs
    .\run.ps1 restart               # Restart the bot
    .\run.ps1 -Build start          # Build and start

"@
}

function Test-Requirements {
    # Check if Docker is installed
    try {
        $null = Invoke-Expression "docker --version" 2>$null
    }
    catch {
        Write-Error-Log "Docker is not installed or not in PATH"
        return $false
    }
    
    # Check if Docker daemon is running
    try {
        $null = Invoke-Expression "docker info" 2>$null
    }
    catch {
        Write-Error-Log "Docker daemon is not running"
        return $false
    }
    
    # Change to project directory
    $projectDir = Split-Path -Parent $PSScriptRoot
    Set-Location $projectDir
    
    # Set compose file based on mode
    if ($Mode -eq "development") {
        $script:composeFile = "docker-compose.dev.yml"
        $script:containerName = "telegram-promo-bot-dev"
        $script:serviceName = "telegram-bot-dev"
    } else {
        $script:composeFile = "docker-compose.yml"
        $script:containerName = "telegram-promo-bot"
        $script:serviceName = "telegram-bot"
    }
    
    # Check if compose file exists
    if (-not (Test-Path $script:composeFile)) {
        Write-Error-Log "Compose file not found: $script:composeFile"
        return $false
    }
    
    # Check if .env file exists
    if (-not (Test-Path ".env")) {
        Write-Error-Log ".env file not found. Please create it from config.env.template"
        return $false
    }
    
    return $true
}

function Start-Container {
    Write-Log "Starting bot in $Mode mode..."
    
    if (-not $Foreground) {
        Invoke-Expression "docker-compose -f $script:composeFile up -d $script:serviceName"
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Bot started successfully in background"
            Write-Log "Container name: $script:containerName"
        }
    } else {
        Write-Log "Starting in foreground mode (Ctrl+C to stop)..."
        Invoke-Expression "docker-compose -f $script:composeFile up $script:serviceName"
    }
}

function Stop-Container {
    Write-Log "Stopping bot..."
    Invoke-Expression "docker-compose -f $script:composeFile down"
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Bot stopped successfully"
    }
}

function Restart-Container {
    Write-Log "Restarting bot..."
    Invoke-Expression "docker-compose -f $script:composeFile restart $script:serviceName"
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Bot restarted successfully"
    }
}

function Show-Logs {
    Write-Log "Showing bot logs (Ctrl+C to exit)..."
    Invoke-Expression "docker-compose -f $script:composeFile logs -f $script:serviceName"
}

function Show-Status {
    Write-Log "Container status:"
    Invoke-Expression "docker-compose -f $script:composeFile ps"
}

# Main execution
if ($Help) {
    Show-Help
    exit 0
}

# Validate mode
if ($Mode -notin @("production", "development")) {
    Write-Error-Log "Invalid mode: $Mode. Must be 'production' or 'development'"
    exit 1
}

Write-Log "Docker management script for Telegram Promo Bot"
Write-Log "Mode: $Mode"

# Check requirements
if (-not (Test-Requirements)) {
    exit 1
}

# Execute command
switch ($Command.ToLower()) {
    "stop" { Stop-Container }
    "restart" { Restart-Container }
    "logs" { Show-Logs }
    "status" { Show-Status }
    "build" { 
        $Build = $true
        Start-Container 
    }
    default { Start-Container }
} 