# 🛠️ Local Dev Environment (Docker + LocalStack)

## 🏗️ Build Process

## Login into AWS SSO profile (or use AWS credentials)

```
aws sso login --profile <sso profile name>
```

### Run Container Locally

```bash
  DOCKER_BUILDKIT=0 docker buildx build --provenance=false --output type=docker --tag upwork-rag-worker-prod:v1.0.0 .
```

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
 1. Deploy CDK stack first (creates ECR repo)
  cd infra && cdk deploy --profile <your aws profile name>

2. Login to ECR
  aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

● To deploy your image to ECR with your AWS SSO profile, follow these steps:

  1. Get ECR Registry URI

  First, get the ECR repository URI from your deployed stack:
```bash
  aws ecr describe-repositories --repository-names rag-worker --profile awsomedevs-prd-mateusz --region eu-central-1
```
  2. Login to ECR
```bash
  aws ecr get-login-password --region eu-central-1 \
  --profile awsomedevs-prd-mateusz \
  | docker login --username AWS --password-stdin 539247473920.dkr.ecr.eu-central-1.amazonaws.com
```

  3. Tag for ECR
```bash
  docker tag upwork-rag-worker-prod:v1.0.0 539247473920.dkr.ecr.eu-central-1.amazonaws.com/upwork-rag-worker-prod:v1.0.0
  docker tag upwork-rag-worker-prod:v1.0.0 539247473920.dkr.ecr.eu-central-1.amazonaws.com/upwork-rag-worker-prod:latest
```
  4. Push to ECR
```bash
  docker push 539247473920.dkr.ecr.eu-central-1.amazonaws.com/upwork-rag-worker-prod:v1.0.0
  docker push 539247473920.dkr.ecr.eu-central-1.amazonaws.com/upwork-rag-worker-prod:latest
```

## 🧪 Test job ingestion

```bash
curl -X POST http://localhost:8080/job \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d @src/sample_job.json
```

## Clean up AWS environment:

```bash
aws sagemaker delete-endpoint --endpoint-name rag-worker-endpoint-prod --profile awsomedevs-prd-mateusz

aws sagemaker create-endpoint \
  --endpoint-name rag-worker-endpoint-prod \
  --endpoint-config-name rag-worker-endpoint-config-prod-1754652110 \
  --region eu-central-1 \
  --profile awsomedevs-prd-mateusz
```