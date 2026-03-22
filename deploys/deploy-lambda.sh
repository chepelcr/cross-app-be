#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}
PROFILE=${2:-J-CAMPOS}
REGION=${3:-us-east-1}

STACK_NAME="cd-backend-${ENVIRONMENT}-lambda"

echo "Deploy Lambda SAM stack"
echo "Environment  -> $ENVIRONMENT"
echo "Profile      -> $PROFILE"
echo ""

# ── SAM CLI via local venv ─────────────────────────────────────────────────────
VENV_DIR=".venv-sam"
if [ ! -f "${VENV_DIR}/bin/sam" ] && [ ! -f "${VENV_DIR}/Scripts/sam" ]; then
  echo "Installing aws-sam-cli in ${VENV_DIR}..."
  py -3 -m venv "$VENV_DIR" 2>/dev/null || python3 -m venv "$VENV_DIR"
  source "${VENV_DIR}/Scripts/activate" 2>/dev/null || source "${VENV_DIR}/bin/activate"
  pip install --quiet aws-sam-cli
else
  source "${VENV_DIR}/Scripts/activate" 2>/dev/null || source "${VENV_DIR}/bin/activate"
fi
echo "SAM CLI: $(sam --version)"
echo ""

# ── Handle stuck stacks ────────────────────────────────────────────────────────
STACK_STATUS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" --region "$REGION" --profile "$PROFILE" \
    --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo "DOES_NOT_EXIST")

if [[ "$STACK_STATUS" =~ ^(ROLLBACK_FAILED|ROLLBACK_COMPLETE|DELETE_FAILED|UPDATE_ROLLBACK_COMPLETE|UPDATE_ROLLBACK_FAILED|CREATE_FAILED)$ ]]; then
  echo "Stack in $STACK_STATUS — deleting before redeploy..."
  aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION" --profile "$PROFILE"
  aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION" --profile "$PROFILE" || true
fi

# ── SAM deploy (image already in ECR via CodePipeline) ────────────────────────
echo "Deploying SAM stack: $STACK_NAME"
sam deploy \
    --config-env "$ENVIRONMENT" \
    --profile "$PROFILE" \
    --resolve-image-repos \
    --no-fail-on-empty-changeset

echo ""
echo "Done: $STACK_NAME"
