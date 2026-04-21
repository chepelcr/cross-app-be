# Deployment Instructions - API Gateway Update

## Current Situation

**Problem**: Frontend is getting CORS errors because the dashboard endpoint (and other new endpoints) don't exist in the deployed API Gateway yet.

**Error**: `No 'Access-Control-Allow-Origin' header is present on the requested resource`

**Root Cause**: The deployed API Gateway only has 23 old endpoints. The new endpoints (dashboard, sessions, assignments, branches, terminals, closings, consecutives) are not deployed yet.

## Solution

### Option A: Automatic Deployment via Pipeline (Recommended)

1. **Commit the changes**:
   ```bash
   cd cross-app-be
   git add api-gateway/template.yml
   git add API_GATEWAY_UPDATE_NOTES.md
   git add DEPLOYMENT_INSTRUCTIONS.md
   git commit -m "feat: add x-user-id header mapping and CORS configuration for new endpoints"
   ```

2. **Push to trigger pipeline**:
   ```bash
   git push origin develop
   ```

3. **Pipeline will automatically**:
   - Refresh swagger/backend.json with ALL endpoints (including dashboard)
   - Regenerate api-gateway/template.yml with complete configuration
   - Deploy updated API Gateway with all new endpoints
   - Configure CORS headers to allow x-user-id

4. **Wait for deployment** (~5-10 minutes)

5. **Test the frontend** - CORS errors should be resolved

### Option B: Manual Deployment (If you have AWS credentials)

1. **Set environment variables**:
   ```bash
   export ENVIRONMENT=dev
   export REGION=us-east-1
   export API_DOMAIN=orders-api.jcampos.dev
   export ROOT_DOMAIN=jcampos.dev
   ```

2. **Run the deployment script**:
   ```bash
   cd cross-app-be
   bash scripts/pipeline-api.sh
   ```

3. **Wait for deployment** (~5-10 minutes)

4. **Test the frontend** - CORS errors should be resolved

## What Gets Deployed

### New Endpoints
- `/api/organizations/{org_id}/dashboard` ← **This is what's failing now**
- `/api/organizations/{org_id}/sessions`
- `/api/organizations/{org_id}/assignments`
- `/api/organizations/{org_id}/branches`
- `/api/organizations/{org_id}/branches/{branch_id}/terminals`
- `/api/organizations/{org_id}/closings`
- `/api/organizations/{org_id}/consecutives`

### CORS Configuration
All endpoints will have:
```yaml
Access-Control-Allow-Headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,x-user-id
Access-Control-Allow-Methods: GET,POST,PUT,PATCH,DELETE,OPTIONS
Access-Control-Allow-Origin: *
```

### Header Injection
API Gateway will automatically:
1. Extract `sub` claim from Cognito JWT
2. Inject it as `x-user-id` header to Lambda
3. Backend receives the header without frontend sending it

## Verification After Deployment

### 1. Test CORS Preflight
```bash
curl -X OPTIONS https://orders-api.jcampos.dev/api/organizations/test/dashboard \
  -H "Origin: http://localhost:9000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: authorization,x-user-id" \
  -v
```

**Expected Response**:
```
< HTTP/2 200
< access-control-allow-headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,x-user-id
< access-control-allow-methods: GET,OPTIONS
< access-control-allow-origin: *
```

### 2. Test Actual Request
```bash
curl https://orders-api.jcampos.dev/api/organizations/{your-org-id}/dashboard \
  -H "Authorization: Bearer {your-jwt-token}" \
  -v
```

**Expected**: Should return dashboard data (or 401 if token is invalid)

### 3. Test Frontend
- Open http://localhost:9000
- Navigate to dashboard
- Should load without CORS errors

## Timeline

- **Commit & Push**: 1 minute
- **Pipeline Build**: 3-5 minutes
- **API Gateway Deployment**: 5-10 minutes
- **Total**: ~10-15 minutes

## Current Status

- ✅ Template generation script is correct
- ✅ All controllers are registered
- ✅ CORS configuration includes x-user-id
- ✅ Header injection is configured
- ❌ Swagger needs refresh (will happen in pipeline)
- ❌ API Gateway needs deployment (will happen in pipeline)

## Next Steps

**Choose Option A or B above and proceed with deployment.**

Once deployed, the frontend will be able to call all new endpoints without CORS errors.
