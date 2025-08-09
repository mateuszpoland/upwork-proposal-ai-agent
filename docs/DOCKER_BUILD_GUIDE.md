# Docker Build and Tagging Guide

## Overview

This guide covers the Docker image build and tagging process for the RAG Worker application. The build system supports multiple environments, semantic versioning, and automated tagging strategies.

## Files

- **Dockerfile**: Located in project root, builds the RAG worker application
- **scripts/build-image.sh**: Comprehensive build script with advanced tagging
- **Makefile**: Simplified build commands for common operations
- **src/rag_worker/requirements.txt**: Python dependencies

## Dockerfile Analysis

### Base Configuration
```dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
```

### Dependencies
- **System packages**: build-essential, libpq-dev, gcc, curl
- **Python packages**: FastAPI, LlamaIndex, OpenAI, Supabase, boto3, uvicorn
- **Total dependencies**: 24 packages including telemetry and debugging tools

### Container Setup
- **Port**: 8080 (EXPOSE 8080)
- **Command**: `uvicorn src.rag_worker.inference:app --host 0.0.0.0 --port 8080`
- **Working Directory**: /app
- **Application Path**: /app/src

## Tagging Strategy

### Supported Tag Formats

1. **Semantic Version Tags**
   - `v1.0.0`, `1.0.0` - Version-specific tags
   - Used for production releases

2. **Environment Tags**
   - `dev-20231203-143022` - Environment with timestamp
   - `dev`, `staging`, `prod` - Environment-specific latest

3. **Git-based Tags**
   - `git-a1b2c3d` - Git commit hash for traceability

4. **Special Tags**
   - `latest` - Most recent build
   - Custom tags via `--tag` parameter

### Tag Examples
```bash
# Development build
rag-worker:dev
rag-worker:dev-20231203-143022
rag-worker:git-a1b2c3d
rag-worker:latest

# Production build
rag-worker:v1.0.0
rag-worker:1.0.0
rag-worker:prod
rag-worker:prod-20231203-143022
rag-worker:git-a1b2c3d
rag-worker:latest
```

## Build Script Usage

### Basic Commands

```bash
# Development build
./scripts/build-image.sh --env dev

# Production build with version
./scripts/build-image.sh --version 1.0.0 --env prod

# Build with ECR registry
./scripts/build-image.sh --env dev --registry 123456789.dkr.ecr.us-east-1.amazonaws.com/rag-worker-dev

# Build and push
./scripts/build-image.sh --env prod --version 1.0.0 --registry ECR_URI --push
```

### Advanced Options

```bash
# No cache build
./scripts/build-image.sh --env dev --no-cache

# Custom tag
./scripts/build-image.sh --env dev --tag my-custom-tag

# Multiple operations
./scripts/build-image.sh --version 1.2.3 --env prod --registry ECR_URI --push --no-cache
```

### Environment Variables

```bash
# Set default ECR registry
export ECR_REGISTRY_URI="123456789.dkr.ecr.us-east-1.amazonaws.com/rag-worker-dev"

# Enable BuildKit (automatically set)
export DOCKER_BUILDKIT=1
```

## Makefile Usage

### Common Commands

```bash
# Show all available commands
make help

# Development workflow
make build-dev          # Build development image
make test-build         # Build without cache for testing

# Production workflow  
make build-prod VERSION=1.0.0    # Build production image
make prod-ready VERSION=1.0.0    # Build and prepare for deployment

# Utility commands
make clean              # Remove built images
```

### With ECR Integration

```bash
# Push development image
make push-dev ECR_URI=123456789.dkr.ecr.us-east-1.amazonaws.com/rag-worker-dev

# Push production image
make push-prod ECR_URI=123456789.dkr.ecr.us-east-1.amazonaws.com/rag-worker-prod VERSION=1.0.0
```

## Build Arguments

The build script automatically passes these arguments to Docker:

```bash
--build-arg VERSION=1.0.0                    # Version number
--build-arg ENVIRONMENT=prod                 # Environment name  
--build-arg GIT_COMMIT=a1b2c3d              # Git commit hash
--build-arg BUILD_TIMESTAMP=20231203-143022  # Build timestamp
```

## Build Process Flow

1. **Validation**
   - Check Dockerfile exists
   - Verify build context
   - Validate parameters

2. **Tag Generation**
   - Generate version tags
   - Create environment tags
   - Add git-based tags
   - Include custom tags

3. **Docker Build**
   - Enable BuildKit
   - Build primary image
   - Tag additional variants

4. **Optional Push**
   - Authenticate with registry
   - Push all tagged images
   - Verify push success

## Local Testing

### Build and Run Locally

```bash
# Build development image
make build-dev

# Run container
docker run -p 8080:8080 rag-worker:latest

# Test endpoints
curl http://localhost:8080/health
```

### Debug Build Issues

```bash
# Build without cache
make test-build

# View build logs
docker build --no-cache -f Dockerfile -t rag-worker:debug .

# Inspect image
docker run -it rag-worker:debug /bin/bash
```

## Environment-Specific Builds

### Development
```bash
./scripts/build-image.sh --env dev
# Creates: rag-worker:dev, rag-worker:dev-{timestamp}, rag-worker:latest
```

### Staging
```bash
./scripts/build-image.sh --env staging --version 1.0.0-rc.1
# Creates: rag-worker:staging, rag-worker:v1.0.0-rc.1, rag-worker:latest
```

### Production
```bash
./scripts/build-image.sh --env prod --version 1.0.0
# Creates: rag-worker:prod, rag-worker:v1.0.0, rag-worker:1.0.0, rag-worker:latest
```

## Integration with ECR

### Repository Format
```
{account-id}.dkr.ecr.{region}.amazonaws.com/rag-worker-{environment}
```

### Build and Push Example
```bash
# Set registry URI
ECR_URI="123456789.dkr.ecr.us-east-1.amazonaws.com/rag-worker-prod"

# Build and push production image
./scripts/build-image.sh \
  --version 1.0.0 \
  --env prod \
  --registry $ECR_URI \
  --push
```

### Authentication
```bash
# ECR login (handled automatically by push script)
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-east-1.amazonaws.com
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   chmod +x scripts/build-image.sh
   ```

2. **Docker BuildKit Not Enabled**
   ```bash
   export DOCKER_BUILDKIT=1
   ```

3. **ECR Authentication Failed**
   ```bash
   aws ecr get-login-password --region your-region | \
     docker login --username AWS --password-stdin your-account.dkr.ecr.region.amazonaws.com
   ```

4. **Build Context Too Large**
   - Add `.dockerignore` file
   - Exclude unnecessary files

### Debugging Commands

```bash
# Check Docker version
docker version

# Verify BuildKit
docker buildx version

# List built images
docker images | grep rag-worker

# Inspect image
docker inspect rag-worker:latest

# Check container logs
docker logs $(docker ps -q --filter ancestor=rag-worker:latest)
```

## Best Practices

### Version Management
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Tag release candidates with `-rc.N` suffix
- Always tag production builds with specific versions

### Build Optimization
- Use multi-stage builds for smaller images
- Leverage Docker layer caching
- Order Dockerfile commands from least to most frequently changing

### Security
- Scan images for vulnerabilities
- Use specific base image versions
- Don't include secrets in images
- Run containers as non-root user

### CI/CD Integration
- Automate builds on code changes
- Use environment-specific pipelines
- Implement automatic testing before push
- Tag builds with CI build numbers

---
**Generated**: $(date)
**Script Version**: 1.0.0
**Docker Version**: 20.10+
**BuildKit**: Required