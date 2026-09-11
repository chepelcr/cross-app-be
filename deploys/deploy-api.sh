#!/bin/bash
# Regenerate api-gateway/template.yml from app/main.py and deploy the API Gateway SAM stack.
# Usage: bash deploys/deploy-api.sh [environment] [profile] [--skip-refresh]

ENVIRONMENT=${1:-dev}
PROFILE=${2:-J-CAMPOS}
SKIP_REFRESH=false

for arg in "$@"; do
  [ "$arg" = "--skip-refresh" ] && SKIP_REFRESH=true
done

echo "Deploy API Gateway"
echo "Environment  -> $ENVIRONMENT"
echo "Profile      -> $PROFILE"
echo ""

# ── Setup venv SAM ────────────────────────────────────────────────────────────
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

# ── Step 1: Regenerate template from app/main.py ──────────────────────────────
if [ "$SKIP_REFRESH" = "true" ]; then
  echo "Skipping swagger refresh (--skip-refresh)"
  python3 scripts/gen_api_template.py --skip-refresh
else
  echo "Refreshing swagger and generating template..."
  python3 scripts/gen_api_template.py
fi

echo ""

# ── Step 2: Resolve Route53 Hosted Zone ID for jcampos.dev ───────────────────
echo "Resolving Route53 hosted zone for jcampos.dev..."
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name \
  --dns-name jcampos.dev \
  --query 'HostedZones[0].Id' \
  --output text \
  --profile "$PROFILE" | sed 's|/hostedzone/||')

if [ -z "$HOSTED_ZONE_ID" ] || [ "$HOSTED_ZONE_ID" = "None" ]; then
  echo "ERROR: Could not resolve hosted zone ID for jcampos.dev"
  exit 1
fi
echo "HostedZoneId -> $HOSTED_ZONE_ID"
echo ""

# ── Step 3: SAM deploy ────────────────────────────────────────────────────────
echo "Deploying API Gateway stack..."
cd api-gateway
sam deploy \
  --config-env "${ENVIRONMENT}" \
  --profile "${PROFILE}" \
  --parameter-overrides "Environment=${ENVIRONMENT} HostedZoneId=${HOSTED_ZONE_ID}" \
  --no-fail-on-empty-changeset

echo ""
echo "Done."
