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
BUILD_TYPE="production"
NO_CACHE=false
VERBOSE=false
PUSH=false
TAG="latest"

# Help function
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Build Docker image for Telegram Promo Bot

OPTIONS:
    -t, --type TYPE         Build type: production (default) or development
    -T, --tag TAG          Docker image tag (default: latest)
    --no-cache             Build without using cache
    --push                 Push image to registry after build
    -v, --verbose          Verbose output
    -h, --help             Show this help message

EXAMPLES:
    $0                     # Build production image
    $0 -t development      # Build development image
    $0 --no-cache -v       # Build with no cache and verbose output
    $0 -T v1.0.0 --push    # Build and push with tag v1.0.0

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            BUILD_TYPE="$2"
            shift 2
            ;;
        -T|--tag)
            TAG="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --push)
            PUSH=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
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

# Validate build type
if [[ "$BUILD_TYPE" != "production" && "$BUILD_TYPE" != "development" ]]; then
    error "Invalid build type: $BUILD_TYPE. Must be 'production' or 'development'"
    exit 1
fi

# Set image name
IMAGE_NAME="telegram-promo-bot"
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

if [[ "$BUILD_TYPE" == "development" ]]; then
    FULL_IMAGE_NAME="${IMAGE_NAME}-dev:${TAG}"
fi

# Build function
build_image() {
    log "Building Docker image: $FULL_IMAGE_NAME"
    log "Build type: $BUILD_TYPE"
    log "Project directory: $PROJECT_DIR"
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    # Check if Dockerfile exists
    if [[ ! -f "Dockerfile" ]]; then
        error "Dockerfile not found in $PROJECT_DIR"
        exit 1
    fi
    
    # Check if .env file exists
    if [[ ! -f ".env" ]]; then
        warn ".env file not found. Make sure to create it from config.env.template"
    fi
    
    # Build command
    local build_cmd="docker build"
    
    # Add build arguments
    build_cmd+=" --target $BUILD_TYPE"
    build_cmd+=" -t $FULL_IMAGE_NAME"
    
    if [[ "$NO_CACHE" == "true" ]]; then
        build_cmd+=" --no-cache"
        log "Building without cache"
    fi
    
    if [[ "$VERBOSE" == "true" ]]; then
        build_cmd+=" --progress=plain"
    fi
    
    # Add build context
    build_cmd+=" ."
    
    log "Executing: $build_cmd"
    
    # Execute build
    if eval "$build_cmd"; then
        success "Docker image built successfully: $FULL_IMAGE_NAME"
    else
        error "Docker build failed"
        exit 1
    fi
}

# Push function
push_image() {
    if [[ "$PUSH" == "true" ]]; then
        log "Pushing image to registry: $FULL_IMAGE_NAME"
        
        if docker push "$FULL_IMAGE_NAME"; then
            success "Image pushed successfully: $FULL_IMAGE_NAME"
        else
            error "Failed to push image"
            exit 1
        fi
    fi
}

# Check Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi
}

# Main execution
main() {
    log "Starting Docker build process..."
    
    check_docker
    build_image
    push_image
    
    success "Build process completed successfully!"
    log "Image: $FULL_IMAGE_NAME"
    
    # Show image info
    log "Image information:"
    docker images "$FULL_IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
}

# Run main function
main 