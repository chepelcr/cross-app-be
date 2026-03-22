#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}
PROFILE=${2:-J-CAMPOS}
REGION=${3:-us-east-1}

STACK_NAME="jcampos-${ENVIRONMENT}-cd-backend-codepipeline"
TEMPLATE="cloudformation/codepipeline.yml"

echo "Deploying CodePipeline stack: $STACK_NAME"

aws cloudformation deploy \
  --template-file "$TEMPLATE" \
  --stack-name "$STACK_NAME" \
  --parameter-overrides Environment="$ENVIRONMENT" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$REGION" \
  --profile "$PROFILE" \
  --no-fail-on-empty-changeset

echo "Stack deployed: $STACK_NAME"
echo ""
echo "To trigger the pipeline manually:"
echo "  aws codepipeline start-pipeline-execution \\"
echo "    --name jcampos-${ENVIRONMENT}-cd-backend-pipeline \\"
echo "    --profile $PROFILE"
