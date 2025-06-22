#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

# Function to check if required environment variables are set
check_env_vars() {
    log "Checking environment variables..."
    
    local required_vars=("TELEGRAM_BOT_TOKEN" "OPENAI_API_KEY")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        error "Missing required environment variables: ${missing_vars[*]}"
        error "Please check your .env file or environment configuration"
        exit 1
    fi
    
    success "All required environment variables are set"
}

# Function to create necessary directories
setup_directories() {
    log "Setting up directories..."
    
    local dirs=("/app/data" "/app/data/logs" "/app/data/backups" "/app/data/user_data")
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log "Created directory: $dir"
        fi
    done
    
    # Set proper permissions
    chmod 755 /app/data
    chmod 755 /app/data/logs
    chmod 755 /app/data/backups
    chmod 755 /app/data/user_data
    
    success "Directory setup completed"
}

# Function to validate Python dependencies
check_dependencies() {
    log "Checking Python dependencies..."
    
    # Check if critical modules can be imported
    python -c "
import sys
try:
    import telegram
    import openai
    import requests
    import flask
    print('✅ All critical dependencies are available')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
    sys.exit(1)
" || {
        error "Dependency check failed"
        exit 1
    }
    
    success "Dependency check passed"
}

# Function to test external connectivity
test_connectivity() {
    log "Testing external connectivity..."
    
    # Test internet connectivity
    if curl -s --max-time 10 https://api.telegram.org > /dev/null; then
        success "Telegram API connectivity: OK"
    else
        warn "Telegram API connectivity: FAILED (may affect bot functionality)"
    fi
    
    if curl -s --max-time 10 https://api.openai.com > /dev/null; then
        success "OpenAI API connectivity: OK"
    else
        warn "OpenAI API connectivity: FAILED (may affect text generation)"
    fi
}

# Function to perform health check
health_check() {
    log "Performing health check..."
    
    # Check if the application can start without errors
    python -c "
import sys
sys.path.append('/app')
try:
    from config import config
    print('✅ Configuration loaded successfully')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    sys.exit(1)
" || {
        error "Health check failed"
        exit 1
    }
    
    success "Health check passed"
}

# Function to start the web dashboard (optional)
start_dashboard() {
    if [[ "${ENABLE_DASHBOARD:-false}" == "true" ]]; then
        log "Starting web dashboard..."
        python web_dashboard.py &
        DASHBOARD_PID=$!
        log "Web dashboard started with PID: $DASHBOARD_PID"
    fi
}

# Function to handle graceful shutdown
cleanup() {
    log "Received shutdown signal, cleaning up..."
    
    if [[ -n "$DASHBOARD_PID" ]]; then
        log "Stopping web dashboard..."
        kill $DASHBOARD_PID 2>/dev/null || true
    fi
    
    if [[ -n "$BOT_PID" ]]; then
        log "Stopping bot..."
        kill $BOT_PID 2>/dev/null || true
        wait $BOT_PID 2>/dev/null || true
    fi
    
    success "Cleanup completed"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Main execution
main() {
    log "Starting Telegram Promo Bot container..."
    log "Environment: ${TELEGRAM_BOT_ENV:-development}"
    
    # Run all checks
    check_env_vars
    setup_directories
    check_dependencies
    test_connectivity
    health_check
    
    # Start optional services
    start_dashboard
    
    success "Container initialization completed"
    log "Starting bot application..."
    
    # Execute the main command
    exec "$@" &
    BOT_PID=$!
    
    # Wait for the bot process
    wait $BOT_PID
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 