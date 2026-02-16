#!/bin/bash

STACK_NAME="crossdocking-s3-stack"
PROFILE="J-CAMPOS"
DOMAIN="jcampos.dev"

echo "🚀 Deploying S3 Bucket Stack"

# Get Hosted Zone ID
echo "🔍 Looking up Hosted Zone ID for ${DOMAIN}..."
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name \
    --query "HostedZones[?Name=='${DOMAIN}.'].Id" \
    --output text \
    --profile $PROFILE | cut -d'/' -f3)

if [ -z "$HOSTED_ZONE_ID" ]; then
    echo "❌ Could not find Hosted Zone for ${DOMAIN}"
    exit 1
fi

echo "✅ Found Hosted Zone ID: $HOSTED_ZONE_ID"

aws cloudformation deploy \
    --template-file ./cloudformation/s3-uploads.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        HostedZoneId="$HOSTED_ZONE_ID" \
    --profile $PROFILE

if [ $? -ne 0 ]; then
    echo "❌ Failed to deploy S3 stack"
    exit 1
fi

echo "✅ S3 bucket deployed successfully!"
