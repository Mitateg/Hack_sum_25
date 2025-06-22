#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
MODE="production"
DETACH=true
BUILD=false
LOGS=false
STOP=false
RESTART=false
STATUS=false

# Help function
show_help() {
    cat << EOF
Usage: $0 [OPTIONS] [COMMAND]

Run Telegram Promo Bot in Docker container

COMMANDS:
    start       Start the bot (default)
    stop        Stop the bot
    restart     Restart the bot
    logs        Show bot logs
    status      Show container status
    build       Build and run the bot

OPTIONS:
    -m, --mode MODE         Run mode: production (default) or development
    -f, --foreground        Run in foreground (don't detach)
    -b, --build             Build image before running
    -h, --help              Show this help message

EXAMPLES:
    $0                      # Start bot in production mode
    $0 -m development       # Start bot in development mode
    $0 stop                 # Stop the bot
    $0 logs                 # Show logs
    $0 restart              # Restart the bot
    $0 -b start             # Build and start
    $0 -f -m development    # Start in development mode in foreground

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        start)
            # Default action, do nothing
            shift
            ;;
        stop)
            STOP=true
            shift
            ;;
        restart)
            RESTART=true
            shift
            ;;
        logs)
            LOGS=true
            shift
            ;;
        status)
            STATUS=true
            shift
            ;;
        build)
            BUILD=true
            shift
            ;;
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -f|--foreground)
            DETACH=false
            shift
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate mode
if [[ "$MODE" != "production" && "$MODE" != "development" ]]; then
    error "Invalid mode: $MODE. Must be 'production' or 'development'"
    exit 1
fi

# Set compose file and container name based on mode
if [[ "$MODE" == "development" ]]; then
    COMPOSE_FILE="docker-compose.dev.yml"
    CONTAINER_NAME="telegram-promo-bot-dev"
    SERVICE_NAME="telegram-bot-dev"
else
    COMPOSE_FILE="docker-compose.yml"
    CONTAINER_NAME="telegram-promo-bot"
    SERVICE_NAME="telegram-bot"
fi

# Check requirements
check_requirements() {
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    # Check if compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Check if .env file exists
    if [[ ! -f ".env" ]]; then
        error ".env file not found. Please create it from config.env.template"
        exit 1
    fi
}

# Build image if requested
build_image() {
    if [[ "$BUILD" == "true" ]]; then
        log "Building Docker image..."
        if [[ -f "$SCRIPT_DIR/build.sh" ]]; then
            bash "$SCRIPT_DIR/build.sh" -t "$MODE"
        else
            # Fallback to docker-compose build
            docker-compose -f "$COMPOSE_FILE" build "$SERVICE_NAME"
        fi
    fi
}

# Start container
start_container() {
    log "Starting bot in $MODE mode..."
    
    local compose_cmd="docker-compose -f $COMPOSE_FILE"
    
    if [[ "$DETACH" == "true" ]]; then
        $compose_cmd up -d "$SERVICE_NAME"
        success "Bot started successfully in background"
        log "Container name: $CONTAINER_NAME"
        log "Use '$0 logs' to view logs"
        log "Use '$0 status' to check status"
    else
        log "Starting in foreground mode (Ctrl+C to stop)..."
        $compose_cmd up "$SERVICE_NAME"
    fi
}

# Stop container
stop_container() {
    log "Stopping bot..."
    docker-compose -f "$COMPOSE_FILE" down
    success "Bot stopped successfully"
}

# Restart container
restart_container() {
    log "Restarting bot..."
    docker-compose -f "$COMPOSE_FILE" restart "$SERVICE_NAME"
    success "Bot restarted successfully"
}

# Show logs
show_logs() {
    log "Showing bot logs (Ctrl+C to exit)..."
    docker-compose -f "$COMPOSE_FILE" logs -f "$SERVICE_NAME"
}

# Show status
show_status() {
    log "Container status:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo ""
    log "Resource usage:"
    if docker stats "$CONTAINER_NAME" --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" 2>/dev/null; then
        :
    else
        warn "Container is not running"
    fi
}

# Main execution
main() {
    log "Docker management script for Telegram Promo Bot"
    log "Mode: $MODE"
    
    check_requirements
    
    if [[ "$STOP" == "true" ]]; then
        stop_container
    elif [[ "$RESTART" == "true" ]]; then
        restart_container
    elif [[ "$LOGS" == "true" ]]; then
        show_logs
    elif [[ "$STATUS" == "true" ]]; then
        show_status
    else
        build_image
        start_container
    fi
}

# Run main function
main 