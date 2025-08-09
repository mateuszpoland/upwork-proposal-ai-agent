# RAG Worker Makefile
# Common Docker build and deployment operations

.PHONY: help build build-dev build-prod test-build push-dev push-prod clean

# Default target
help:
	@echo "RAG Worker Build Commands"
	@echo "========================"
	@echo ""
	@echo "Docker Build Commands:"
	@echo "  build-dev     - Build development image"
	@echo "  build-prod    - Build production image with version"
	@echo "  build-latest  - Build and tag as latest"
	@echo "  test-build    - Test build without cache"
	@echo ""
	@echo "Registry Commands:"
	@echo "  push-dev      - Push development image to ECR"
	@echo "  push-prod     - Push production image to ECR"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean         - Remove built images"
	@echo "  run-local     - Run container locally"
	@echo "  logs          - Show container logs"
	@echo ""
	@echo "Variables:"
	@echo "  VERSION       - Version tag (default: 1.0.0)"
	@echo "  ECR_URI       - ECR repository URI"
	@echo ""
	@echo "Examples:"
	@echo "  make build-dev"
	@echo "  make build-prod VERSION=1.2.3"
	@echo "  make push-dev ECR_URI=123456789.dkr.ecr.us-east-1.amazonaws.com/rag-worker-dev"

# Variables
VERSION ?= 1.0.0
ECR_URI ?= 
PROJECT_NAME = rag-worker
BUILD_SCRIPT = ./scripts/build-image.sh

# Ensure build script exists and is executable
$(BUILD_SCRIPT):
	@echo "Build script not found or not executable"
	@chmod +x $(BUILD_SCRIPT) 2>/dev/null || true

# Development build
build-dev: $(BUILD_SCRIPT)
	@echo "Building development image..."
	$(BUILD_SCRIPT) --env dev --latest

# Production build with version
build-prod: $(BUILD_SCRIPT)
	@echo "Building production image version $(VERSION)..."
	$(BUILD_SCRIPT) --version $(VERSION) --env prod --latest

# Build latest only
build-latest: $(BUILD_SCRIPT)
	@echo "Building latest image..."
	$(BUILD_SCRIPT) --env dev

# Test build without cache
test-build: $(BUILD_SCRIPT)
	@echo "Test building without cache..."
	$(BUILD_SCRIPT) --env test --no-cache

# Build with custom version
build: $(BUILD_SCRIPT)
	@echo "Building version $(VERSION)..."
	$(BUILD_SCRIPT) --version $(VERSION)

# Clean up built images
clean:
	@echo "Cleaning up images..."
	@docker images | grep $(PROJECT_NAME) | awk '{print $$3}' | xargs -r docker rmi -f
	@echo "Cleanup completed"