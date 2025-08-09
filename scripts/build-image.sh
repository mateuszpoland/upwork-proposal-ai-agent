#!/bin/bash

# RAG Worker Docker Image Build Script
# This script builds and tags Docker images for the RAG worker application

set -euo pipefail

# Configuration
PROJECT_NAME="rag-worker"
DOCKER_FILE="Dockerfile"
BUILD_CONTEXT="."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
RAG Worker Docker Build Script

Usage: $0 [OPTIONS]

Options:
    -v, --version VERSION     Semantic version (e.g., 1.0.0)
    -e, --env ENVIRONMENT     Environment (dev, staging, prod)
    -r, --registry REGISTRY   ECR registry URI (optional)
    -t, --tag TAG            Additional custom tag
    --latest                 Also tag as 'latest' (default: true)
    --no-cache               Build without cache
    --push                   Push images after building
    -h, --help               Show this help message

Examples:
    $0 --version 1.0.0 --env dev
    $0 --version 1.2.3 --env prod --registry 123456789.dkr.ecr.us-east-1.amazonaws.com/rag-worker-prod
    $0 --env dev --push --no-cache

Environment Variables:
    ECR_REGISTRY_URI         Default ECR registry URI
    DOCKER_BUILDKIT          Enable BuildKit (default: 1)
EOF
}

# Default values
VERSION=""
ENVIRONMENT=""
REGISTRY_URI="${ECR_REGISTRY_URI:-}"
CUSTOM_TAG=""
TAG_LATEST=true
NO_CACHE=false
PUSH_IMAGES=false
ADDITIONAL_TAGS=()

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY_URI="$2"
            shift 2
            ;;
        -t|--tag)
            CUSTOM_TAG="$2"
            shift 2
            ;;
        --latest)
            TAG_LATEST=true
            shift
            ;;
        --no-latest)
            TAG_LATEST=false
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --push)
            PUSH_IMAGES=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate inputs
if [[ -z "$VERSION" && -z "$ENVIRONMENT" ]]; then
    log_error "Either --version or --env must be specified"
    show_help
    exit 1
fi

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")

# Get git commit hash if available
GIT_COMMIT=""
if command -v git &> /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
    GIT_COMMIT=$(git rev-parse --short HEAD)
fi

# Prepare base image name
if [[ -n "$REGISTRY_URI" ]]; then
    BASE_IMAGE="$REGISTRY_URI"
else
    BASE_IMAGE="$PROJECT_NAME"
fi

# Prepare tags
TAGS=()

# Version-based tag
if [[ -n "$VERSION" ]]; then
    # Remove 'v' prefix if present
    VERSION=$(echo "$VERSION" | sed 's/^v//')
    TAGS+=("$BASE_IMAGE:v$VERSION")
    TAGS+=("$BASE_IMAGE:$VERSION")
fi

# Environment-based tag
if [[ -n "$ENVIRONMENT" ]]; then
    TAGS+=("$BASE_IMAGE:$ENVIRONMENT-$TIMESTAMP")
    TAGS+=("$BASE_IMAGE:$ENVIRONMENT")
fi

# Git-based tag
if [[ -n "$GIT_COMMIT" ]]; then
    TAGS+=("$BASE_IMAGE:git-$GIT_COMMIT")
fi

# Custom tag
if [[ -n "$CUSTOM_TAG" ]]; then
    TAGS+=("$BASE_IMAGE:$CUSTOM_TAG")
fi

# Latest tag
if [[ "$TAG_LATEST" == true ]]; then
    TAGS+=("$BASE_IMAGE:latest")
fi

# Ensure we have at least one tag
if [[ ${#TAGS[@]} -eq 0 ]]; then
    log_error "No tags generated. Check your input parameters."
    exit 1
fi

# Display build information
log_info "Starting Docker build process..."
log_info "Project: $PROJECT_NAME"
log_info "Dockerfile: $DOCKER_FILE"
log_info "Build context: $BUILD_CONTEXT"
[[ -n "$VERSION" ]] && log_info "Version: $VERSION"
[[ -n "$ENVIRONMENT" ]] && log_info "Environment: $ENVIRONMENT"
[[ -n "$GIT_COMMIT" ]] && log_info "Git commit: $GIT_COMMIT"
log_info "Timestamp: $TIMESTAMP"
log_info "Tags to be created:"
for tag in "${TAGS[@]}"; do
    log_info "  - $tag"
done

# Check if Dockerfile exists
if [[ ! -f "$DOCKER_FILE" ]]; then
    log_error "Dockerfile not found: $DOCKER_FILE"
    exit 1
fi

# Check if build context exists
if [[ ! -d "$BUILD_CONTEXT" ]]; then
    log_error "Build context directory not found: $BUILD_CONTEXT"
    exit 1
fi

# Enable BuildKit
export DOCKER_BUILDKIT=1

# Prepare build args
BUILD_ARGS=()
[[ -n "$VERSION" ]] && BUILD_ARGS+=(--build-arg "VERSION=$VERSION")
[[ -n "$ENVIRONMENT" ]] && BUILD_ARGS+=(--build-arg "ENVIRONMENT=$ENVIRONMENT")
[[ -n "$GIT_COMMIT" ]] && BUILD_ARGS+=(--build-arg "GIT_COMMIT=$GIT_COMMIT")
BUILD_ARGS+=(--build-arg "BUILD_TIMESTAMP=$TIMESTAMP")

# Add cache options
if [[ "$NO_CACHE" == true ]]; then
    BUILD_ARGS+=(--no-cache)
fi

# Build the primary image
PRIMARY_TAG="${TAGS[0]}"
log_info "Building primary image: $PRIMARY_TAG"

docker build \
    "${BUILD_ARGS[@]}" \
    -f "$DOCKER_FILE" \
    -t "$PRIMARY_TAG" \
    "$BUILD_CONTEXT"

if [[ $? -eq 0 ]]; then
    log_success "Primary image built successfully: $PRIMARY_TAG"
else
    log_error "Failed to build primary image"
    exit 1
fi

# Tag additional images
for ((i=1; i<${#TAGS[@]}; i++)); do
    tag="${TAGS[$i]}"
    log_info "Tagging image: $tag"
    docker tag "$PRIMARY_TAG" "$tag"
    if [[ $? -eq 0 ]]; then
        log_success "Tagged: $tag"
    else
        log_error "Failed to tag: $tag"
        exit 1
    fi
done

# Display image information
log_info "Image build completed successfully!"
log_info "Available images:"
for tag in "${TAGS[@]}"; do
    SIZE=$(docker images --format "table {{.Size}}" "$tag" | tail -n 1)
    log_info "  - $tag ($SIZE)"
done

# Push images if requested
if [[ "$PUSH_IMAGES" == true ]]; then
    if [[ -z "$REGISTRY_URI" ]]; then
        log_warning "Push requested but no registry URI provided. Skipping push."
    else
        log_info "Pushing images to registry..."
        for tag in "${TAGS[@]}"; do
            if [[ "$tag" == *"$REGISTRY_URI"* ]]; then
                log_info "Pushing: $tag"
                docker push "$tag"
                if [[ $? -eq 0 ]]; then
                    log_success "Pushed: $tag"
                else
                    log_error "Failed to push: $tag"
                    exit 1
                fi
            else
                log_info "Skipping local tag: $tag"
            fi
        done
        log_success "All images pushed successfully!"
    fi
fi

# Final summary
log_success "Build process completed!"
log_info "To run the container locally:"
log_info "  docker run -p 8080:8080 $PRIMARY_TAG"
log_info ""
log_info "To push images manually:"
for tag in "${TAGS[@]}"; do
    if [[ "$tag" == *"."* ]]; then  # Likely contains registry URI
        log_info "  docker push $tag"
    fi
done