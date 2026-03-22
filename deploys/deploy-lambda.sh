#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}
REGION=${2:-us-east-1}
PROFILE="J-CAMPOS"

ECR_REPO="cd-backend-ecr"
FUNCTION_NAME="cd-backend-${ENVIRONMENT}-lambda"

echo "Deploying cd-backend for environment: $ENVIRONMENT in region: $REGION"

# Validate AWS credentials
echo "Checking AWS credentials..."
aws sts get-caller-identity --profile $PROFILE > /dev/null 2>&1 || {
    echo "AWS credentials expired or invalid."
    exit 1
}
echo "AWS credentials valid"

ACCOUNT_ID=$(aws sts get-caller-identity --profile $PROFILE --query Account --output text)

# Create ECR repository if it doesn't exist
echo "Creating ECR repository if needed..."
aws ecr describe-repositories --repository-names $ECR_REPO --region $REGION --profile $PROFILE > /dev/null 2>&1 || \
aws ecr create-repository --repository-name $ECR_REPO --region $REGION --profile $PROFILE > /dev/null 2>&1

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region $REGION --profile $PROFILE \
    | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com > /dev/null 2>&1

# Build Docker image
echo "Building Docker image..."
docker buildx build --platform linux/amd64 -t $ECR_REPO:latest .

# Tag and push
echo "Pushing Docker image to ECR..."
docker tag $ECR_REPO:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:latest > /dev/null 2>&1

# Deploy SAM stack
echo "Deploying SAM stack..."
sam deploy \
    --config-env $ENVIRONMENT \
    --profile $PROFILE \
    --resolve-image-repos \
    --no-fail-on-empty-changeset

# Update Lambda function code
echo "Updating Lambda function code..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --image-uri "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:latest" \
    --region $REGION \
    --profile $PROFILE > /dev/null 2>&1 || true

echo "Deployment completed: $FUNCTION_NAME"
