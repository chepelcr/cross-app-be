#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}
PROFILE=${2:-PACIFIC-PROD}
REGION=${3:-us-east-1}

STACK_NAME="cd-backend-${ENVIRONMENT}-lambda"

echo "Deploy Lambda SAM stack"
echo "Environment  -> $ENVIRONMENT"
echo "Profile      -> $PROFILE"
echo ""

# ── SAM CLI via local venv ─────────────────────────────────────────────────────
# Prefer a sam already on PATH (install once with: brew install aws-sam-cli).
# Fall back to a local venv only when there isn't one. This bootstrap used to
# run unconditionally and reach for the Windows `py -3` launcher, which does
# not exist on macOS/Linux — so it printed "Installing aws-sam-cli..." and then
# left no sam behind, and the deploy died on the next line.
if ! command -v sam >/dev/null 2>&1; then
  VENV_DIR=".venv-sam"
  if [ ! -x "${VENV_DIR}/bin/sam" ] && [ ! -x "${VENV_DIR}/Scripts/sam" ]; then
    echo "No sam on PATH; installing aws-sam-cli into ${VENV_DIR}..."
    python3 -m venv "$VENV_DIR" || { echo "ERROR: could not create $VENV_DIR"; exit 1; }
    # shellcheck disable=SC1091
    source "${VENV_DIR}/Scripts/activate" 2>/dev/null || source "${VENV_DIR}/bin/activate"
    pip install --quiet aws-sam-cli || { echo "ERROR: could not install aws-sam-cli"; exit 1; }
  else
    # shellcheck disable=SC1091
    source "${VENV_DIR}/Scripts/activate" 2>/dev/null || source "${VENV_DIR}/bin/activate"
  fi
fi
command -v sam >/dev/null 2>&1 || {
  echo "ERROR: sam not found. Install it with: brew install aws-sam-cli"; exit 1; }
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
