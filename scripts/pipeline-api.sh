#!/bin/bash
set -euo pipefail

ENVIRONMENT="${ENVIRONMENT:-dev}"
REGION="${REGION:-us-east-1}"
API_DOMAIN="${API_DOMAIN:-orders-api.jcampos.dev}"
ROOT_DOMAIN="${ROOT_DOMAIN:-jcampos.dev}"

echo "=== API Gateway Update ==="
echo "  Environment : $ENVIRONMENT"
echo "  Region      : $REGION"
echo "  API Domain  : $API_DOMAIN"
echo "  Root Domain : $ROOT_DOMAIN"
echo ""

# Step 1: Regenerate swagger/backend.json + api-gateway/template.yml from app/main.py
echo "Regenerating swagger spec and api-gateway/template.yml..."
python3 scripts/gen_api_template.py
echo ""

# Step 2: Resolve Route53 hosted zone
echo "Resolving Route53 hosted zone for ${ROOT_DOMAIN}..."
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones \
  --query "HostedZones[?Name=='${ROOT_DOMAIN}.'].Id" \
  --output text | sed 's|/hostedzone/||')

if [ -z "$HOSTED_ZONE_ID" ]; then
  echo "ERROR: Could not resolve hosted zone for ${ROOT_DOMAIN}"
  exit 1
fi
echo "  Hosted Zone : $HOSTED_ZONE_ID"
echo ""

# Step 3: SAM deploy — cd into api-gateway/ so samconfig.toml is auto-discovered
echo "Deploying API Gateway stack..."
cd api-gateway
sam deploy \
  --config-env "$ENVIRONMENT" \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset \
  --region "$REGION" \
  --parameter-overrides \
    "Environment=$ENVIRONMENT" \
    "HostedZoneId=$HOSTED_ZONE_ID"
cd ..

echo ""
echo "API Gateway update complete."
