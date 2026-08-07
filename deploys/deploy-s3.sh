#!/bin/bash

set -euo pipefail

STACK_NAME="crossdocking-s3-stack"
PROFILE="PACIFIC-PROD"
REGION="us-east-1"
ROOT_DOMAIN="jcampos.dev"
BUCKET_NAME="tsuru-uploads-dev"
UPLOADS_DOMAIN="uploads.tsuru.jcampos.dev"
FRONTEND_DOMAIN="app.tsuru.jcampos.dev"

echo "🚀 Deploying S3 Bucket Stack"

# Get Hosted Zone ID
echo "🔍 Looking up Hosted Zone ID for ${ROOT_DOMAIN}..."
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name \
    --query "HostedZones[?Name=='${ROOT_DOMAIN}.'].Id" \
    --output text \
    --profile $PROFILE | cut -d'/' -f3)

if [ -z "$HOSTED_ZONE_ID" ]; then
    echo "❌ Could not find Hosted Zone for ${ROOT_DOMAIN}"
    exit 1
fi

echo "✅ Found Hosted Zone ID: $HOSTED_ZONE_ID"

aws cloudformation deploy \
    --template-file ./cloudformation/s3-uploads.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        BucketName="$BUCKET_NAME" \
        DomainName="$UPLOADS_DOMAIN" \
        FrontEndDomainName="$FRONTEND_DOMAIN" \
        HostedZoneId="$HOSTED_ZONE_ID" \
    --region $REGION \
    --profile $PROFILE

echo "✅ S3 bucket deployed successfully!"
echo "   Bucket: https://${BUCKET_NAME}.s3.${REGION}.amazonaws.com"
echo "   CDN:    https://${UPLOADS_DOMAIN}"
