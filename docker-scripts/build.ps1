# PowerShell script for building Docker images on Windows
param(
    [string]$Type = "production",
    [string]$Tag = "latest",
    [switch]$NoCache,
    [switch]$Push,
    [switch]$Verbose,
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
    @"
Usage: .\build.ps1 [OPTIONS]

Build Docker image for Telegram Promo Bot

OPTIONS:
    -Type TYPE          Build type: production (default) or development
    -Tag TAG           Docker image tag (default: latest)
    -NoCache           Build without using cache
    -Push              Push image to registry after build
    -Verbose           Verbose output
    -Help              Show this help message

EXAMPLES:
    .\build.ps1                    # Build production image
    .\build.ps1 -Type development  # Build development image
    .\build.ps1 -NoCache -Verbose  # Build with no cache and verbose output
    .\build.ps1 -Tag v1.0.0 -Push  # Build and push with tag v1.0.0

"@
}

function Test-Docker {
    try {
        $null = docker --version
        $null = docker info
        return $true
    }
    catch {
        Write-Error-Log "Docker is not installed or not running"
        return $false
    }
}

function Build-Image {
    param([string]$ImageName, [string]$BuildType)
    
    Write-Log "Building Docker image: $ImageName"
    Write-Log "Build type: $BuildType"
    
    # Change to project directory
    $projectDir = Split-Path -Parent $PSScriptRoot
    Set-Location $projectDir
    
    # Check if Dockerfile exists
    if (-not (Test-Path "Dockerfile")) {
        Write-Error-Log "Dockerfile not found in $projectDir"
        exit 1
    }
    
    # Check if .env file exists
    if (-not (Test-Path ".env")) {
        Write-Warning ".env file not found. Make sure to create it from config.env.template"
    }
    
    # Build command
    $buildCmd = @("docker", "build")
    $buildCmd += "--target", $BuildType
    $buildCmd += "-t", $ImageName
    
    if ($NoCache) {
        $buildCmd += "--no-cache"
        Write-Log "Building without cache"
    }
    
    if ($Verbose) {
        $buildCmd += "--progress=plain"
    }
    
    $buildCmd += "."
    
    Write-Log "Executing: $($buildCmd -join ' ')"
    
    # Execute build
    $result = & $buildCmd[0] $buildCmd[1..($buildCmd.Length-1)]
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker image built successfully: $ImageName"
    } else {
        Write-Error-Log "Docker build failed"
        exit 1
    }
}

function Push-Image {
    param([string]$ImageName)
    
    if ($Push) {
        Write-Log "Pushing image to registry: $ImageName"
        
        docker push $ImageName
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Image pushed successfully: $ImageName"
        } else {
            Write-Error-Log "Failed to push image"
            exit 1
        }
    }
}

# Main execution
if ($Help) {
    Show-Help
    exit 0
}

# Validate build type
if ($Type -notin @("production", "development")) {
    Write-Error-Log "Invalid build type: $Type. Must be 'production' or 'development'"
    exit 1
}

# Set image name
$imageName = "telegram-promo-bot"
$fullImageName = "${imageName}:${Tag}"

if ($Type -eq "development") {
    $fullImageName = "${imageName}-dev:${Tag}"
}

Write-Log "Starting Docker build process..."

# Check Docker
if (-not (Test-Docker)) {
    exit 1
}

# Build image
Build-Image -ImageName $fullImageName -BuildType $Type

# Push image if requested
Push-Image -ImageName $fullImageName

Write-Success "Build process completed successfully!"
Write-Log "Image: $fullImageName"

# Show image info
Write-Log "Image information:"
docker images $fullImageName --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" 