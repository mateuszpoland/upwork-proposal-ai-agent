# 🛠️ Local Dev Environment (Docker + LocalStack)

## 🏗️ Build Process

## Login into AWS SSO profile (or use AWS credentials)

```
aws sso login --profile awsomedevs-prd-mateusz
```

### Build Docker Images

```bash
# Build with specific version
./scripts/build-images.sh --env dev --version 1.0.0

# Available tags after build:
# - rag-worker:v1.0.0
# - rag-worker:1.0.0  
# - rag-worker:dev-YYYYMMDD-HHMMSS
# - rag-worker:dev
# - rag-worker:git-<commit-hash>
# - rag-worker:latest
```

### Run Container Locally

```bash
# Run specific version
docker run -p 8080:8080 rag-worker:v1.0.0

# Or run latest
docker run -p 8080:8080 rag-worker:latest
```

## ✅ Run local AWS services + database + app

### Using Docker Compose with Built Images

```bash
# Use specific version
APP_RELEASE=v1.0.0 docker-compose up

# Use latest (default)
docker-compose up

# Alternative version tags
APP_RELEASE=1.0.0 docker-compose up
APP_RELEASE=dev docker-compose up
```

### ECR Deployment (Requires AWS Infrastructure)

**Note**: Image pushing to ECR requires the CDK stack to be deployed first to create the ECR repository and proper IAM permissions.

```bash
# 1. Deploy CDK stack first (creates ECR repo)
# cd infra && cdk deploy --profile <your aws profile name>

# 2. Login to ECR
# aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com



  # Build locally first
  ./scripts/build-image.sh --version 1.0.0 --env prod

  The CORRECT build command with flags:
  ```
  DOCKER_BUILDKIT=0 docker buildx build --provenance=false --output type=docker --tag upwork-rag-worker-prod:v1.0.0 .
  ```
```

● To deploy your image to ECR with your AWS SSO profile, follow these steps:

  1. Get ECR Registry URI

  First, get the ECR repository URI from your deployed stack:
  aws ecr describe-repositories --repository-names rag-worker --profile awsomedevs-prd-mateusz --region eu-central-1

  2. Login to ECR

  aws ecr get-login-password --region eu-central-1 \
  --profile awsomedevs-prd-mateusz \
  | docker login --username AWS --password-stdin 539247473920.dkr.ecr.eu-central-1.amazonaws.com

  3. Build and Push with Your Script

  Using your existing script with the ECR registry:
  # Build and push in one command
  ./scripts/build-image.sh \
    --version 1.0.0 \
    --env prod \
    --registry 539247473920.dkr.ecr.eu-central-1.amazonaws.com/rag-worker \
    --push

  4. Alternative: Manual Steps

  If you prefer manual control:
  # Build locally first
  ./scripts/build-image.sh --version 1.0.0 --env prod

  # Tag for ECR
  docker tag upwork-rag-worker-prod:v1.0.0 539247473920.dkr.ecr.eu-central-1.amazonaws.com/upwork-rag-worker-prod:v1.0.0
  docker tag upwork-rag-worker-prod:v1.0.0 539247473920.dkr.ecr.eu-central-1.amazonaws.com/upwork-rag-worker-prod:latest

  # Push to ECR
  docker push 539247473920.dkr.ecr.eu-central-1.amazonaws.com/upwork-rag-worker-prod:v1.0.0
  docker push 539247473920.dkr.ecr.eu-central-1.amazonaws.com/upwork-rag-worker-prod:latest


## 🧪 Test job ingestion

```bash
curl -X POST http://localhost:8080/job \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d @src/sample_job.json
```