#!/bin/bash
set -e

ENVIRONMENT=${ENVIRONMENT:-dev}
REGION=${REGION:-us-east-1}

ECR_REPO="cd-backend-ecr"
FUNCTION_NAME="cd-backend-${ENVIRONMENT}-lambda"

echo "=== Updating cd-backend Lambda function ==="
echo "Environment: $ENVIRONMENT | Region: $REGION"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
IMAGE_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO}:latest"

FAILED=0
SKIPPED=0
UPDATED=0

# Check if Lambda function exists
if ! aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" > /dev/null 2>&1; then
  echo "[SKIP] $FUNCTION_NAME — function not found"
  SKIPPED=1
else
  # Update with retry on throttle
  SUCCESS=0
  for attempt in 1 2 3; do
    if aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --image-uri "$IMAGE_URI" \
        --region "$REGION" > /dev/null 2>&1; then
      echo "[OK] $FUNCTION_NAME"
      SUCCESS=1
      UPDATED=1
      break
    fi
    echo "[RETRY $attempt] $FUNCTION_NAME — waiting 10s..."
    sleep 10
  done

  if [ $SUCCESS -eq 0 ]; then
    echo "[FAIL] $FUNCTION_NAME — update failed after 3 attempts"
    FAILED=1
  fi
fi

echo ""
echo "Total: 1 | Updated: $UPDATED | Skipped: $SKIPPED | Failed: $FAILED"

[ $FAILED -eq 0 ] || exit 1
