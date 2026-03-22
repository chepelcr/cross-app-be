# Cross-Docking Backend API - Deployment Guide

This guide explains how to deploy the Cross-Docking Backend API to AWS Lambda using SAM (Serverless Application Model).

## Prerequisites

1. **AWS CLI** installed and configured
2. **AWS SAM CLI** installed
3. **Docker** installed and running
4. **AWS SSO** configured with profile:
   - `J-CAMPOS` for all environments

## Configuration

### 1. Environment Variables

Create or update your `.env` file with the required variables:

```env
DATABASE_HOST=your-database-host
DATABASE_PORT=5432
DATABASE_USERNAME=your-db-user
DATABASE_PASSWORD=your-db-password
DATABASE_DBNAME=your-db-name

S3_BUCKET=your-s3-bucket
PDF_DOMAIN=https://your-cloudfront-domain
CLOUDFRONT_DISTRIBUTION_ID=your-distribution-id

EMAIL_SENDER=sender@example.com
EMAIL_RECIPIENT=recipient@example.com

API_SERVICES_URL=http://your-api-url
API_ORGANIZATIONS_URL=/api/organizations/%s

PATH_TO_WKHTMLTOPDF=/usr/local/bin/wkhtmltopdf
```

The build script will automatically read these values from `.env` and pass them to the Lambda function.

### 2. Update samconfig.toml (Optional)

If not using the build script, edit `samconfig.toml` and replace the placeholder values for each environment:

```toml
parameter_overrides = "Environment=dev DatabaseHost=<DB_HOST> DatabasePort=5432 DatabaseName=crossdocking DatabaseUser=<DB_USER> DatabasePassword=<DB_PASSWORD> S3BucketName=<S3_BUCKET> CorsOrigin=* PdfDomain=<PDF_DOMAIN> CloudFrontDistributionId=<CF_DIST_ID> EmailSender=<EMAIL_SENDER> EmailRecipient=<EMAIL_RECIPIENT> ApiServicesUrl=<API_SERVICES_URL> ApiOrganizationsUrl=/api/organizations/%s PathToWkhtmltopdf=/usr/local/bin/wkhtmltopdf"
```

Replace:
- `<DB_HOST>` - PostgreSQL database host
- `<DB_USER>` - Database username
- `<DB_PASSWORD>` - Database password
- `<S3_BUCKET>` - S3 bucket name
- `<PDF_DOMAIN>` - CloudFront domain for PDFs
- `<CF_DIST_ID>` - CloudFront distribution ID
- `<EMAIL_SENDER>` - Email sender address
- `<EMAIL_RECIPIENT>` - Email recipient address
- `<API_SERVICES_URL>` - API services base URL

### 3. S3 Buckets

Ensure the following S3 buckets exist for SAM deployments:
- `cross-docking-dev-sam-deployments` (dev)
- `cross-docking-stag-sam-deployments` (staging)
- `cross-docking-prod-sam-deployments` (production)

## Deployment

### Quick Deploy

Use the build script to deploy to any environment:

```bash
# Deploy to development
./scripts/build-lambda.sh dev us-east-1

# Deploy to staging
./scripts/build-lambda.sh stag us-east-1

# Deploy to production
./scripts/build-lambda.sh prod us-east-1
```

### Manual Deployment Steps

If you prefer to deploy manually:

#### 1. Login to AWS SSO

```bash
aws sso login --profile J-CAMPOS
```

#### 2. Get AWS Account ID

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --profile J-CAMPOS --query Account --output text)
```

#### 3. Create ECR Repository (first time only)

```bash
aws ecr create-repository \
  --repository-name cross-docking-backend-ecr \
  --region us-east-1 \
  --profile J-CAMPOS
```

#### 4. Login to ECR

```bash
aws ecr get-login-password --region us-east-1 --profile J-CAMPOS | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

#### 5. Build Docker Image

```bash
docker buildx build --platform linux/amd64 -t cross-docking-backend-ecr:latest .
```

#### 6. Tag and Push to ECR

```bash
docker tag cross-docking-backend-ecr:latest \
  $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/cross-docking-backend-ecr:latest

docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/cross-docking-backend-ecr:latest
```

#### 7. Deploy with SAM

```bash
sam deploy --config-env dev --profile J-CAMPOS --resolve-image-repos --force-upload
```

#### 8. Update Lambda Function Code

```bash
aws lambda update-function-code \
  --function-name cross-docking-dev-backend-api-lambda \
  --image-uri $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/cross-docking-backend-ecr:latest \
  --region us-east-1 \
  --profile J-CAMPOS
```

## Database Migrations

After deployment, run database migrations:

```bash
# SSH into a bastion host or use AWS Systems Manager Session Manager
# Then run:
python -m alembic upgrade head
```

## Verify Deployment

Check the Lambda function logs:

```bash
aws logs tail /aws/lambda/cross-docking-dev-backend-api-lambda \
  --follow \
  --profile J-CAMPOS
```

## Outputs

After successful deployment, SAM will output:
- **Lambda Function ARN**: The ARN of the deployed Lambda function
- **Lambda Function Name**: The name of the Lambda function
- **S3 Bucket Name**: The S3 bucket for file uploads

## Troubleshooting

### Docker Build Issues

If you encounter Docker build issues:
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker buildx build --no-cache --platform linux/amd64 -t cross-docking-backend-ecr:latest .
```

### ECR Push Issues

If ECR push fails:
```bash
# Re-login to ECR
aws ecr get-login-password --region us-east-1 --profile J-CAMPOS | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

### Lambda Function Not Updating

If the Lambda function doesn't update:
```bash
# Force update
aws lambda update-function-code \
  --function-name cross-docking-dev-backend-api-lambda \
  --image-uri $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/cross-docking-backend-ecr:latest \
  --region us-east-1 \
  --profile J-CAMPOS \
  --publish
```

## Architecture

```
┌─────────────────┐
│   API Gateway   │
│   or ALB        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Lambda Function│
│   (FastAPI)     │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌──────┐  ┌──────┐
│  RDS │  │  S3  │
│ (PG) │  │      │
└──────┘  └──────┘
```

## Environment Variables

The Lambda function uses the following environment variables (set via CloudFormation):

- `ENVIRONMENT` - Environment name (dev/stag/prod)
- `STAGE` - Stage configuration (DEVELOPMENT/STAGING/PRODUCTION)
- `DATABASE_HOST` - PostgreSQL host
- `DATABASE_PORT` - PostgreSQL port
- `DATABASE_NAME` - Database name
- `DATABASE_USER` - Database username
- `DATABASE_PASSWORD` - Database password
- `DATABASE_USERNAME` - Database username (alias)
- `DATABASE_DBNAME` - Database name (alias)
- `S3_BUCKET` - S3 bucket for uploads
- `CORS_ORIGIN` - CORS allowed origin
- `PDF_DOMAIN` - CloudFront domain for PDFs
- `CLOUDFRONT_DISTRIBUTION_ID` - CloudFront distribution ID
- `EMAIL_SENDER` - Email sender address
- `EMAIL_RECIPIENT` - Email recipient address
- `API_SERVICES_URL` - API services base URL
- `API_ORGANIZATIONS_URL` - API organizations URL pattern
- `PATH_TO_WKHTMLTOPDF` - Path to wkhtmltopdf binary

## Cost Optimization

- Lambda uses x86_64 architecture for compatibility with wkhtmltopdf
- Log retention is set to 7 days
- Memory is set to 1024 MB (adjust based on usage)
- Timeout is set to 60 seconds

## Security

- Database credentials are passed as parameters (consider using AWS Secrets Manager)
- S3 bucket has CORS configured
- IAM role follows least privilege principle
