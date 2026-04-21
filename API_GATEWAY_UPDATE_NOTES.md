# API Gateway Update Notes

## Issue
Frontend is getting CORS errors when calling new endpoints (dashboard, sessions, assignments, branches, terminals, closings, consecutives) because:
1. These endpoints are not in the deployed API Gateway configuration
2. The `x-user-id` header needs to be allowed in CORS preflight responses

## Solution

### 1. Template Generation Script (`scripts/gen_api_template.py`)
The script already includes the correct configuration:
- **Line 168**: CORS headers include `x-user-id` in `Access-Control-Allow-Headers`
- **Lines 285-286**: Request parameter mapping: `integration.request.header.x-user-id: context.authorizer.claims.sub`
- **Lines 324-336**: Gateway responses include `x-user-id` in CORS headers

### 2. Current Status
- ✅ Template generation script is correct
- ✅ All new controllers are registered in `fast_api_config.py`
- ⚠️ Swagger refresh timed out locally (database connection issue)
- ⚠️ Template was regenerated with existing swagger (missing new endpoints)

### 3. Deployment Steps

The pipeline will automatically:
1. **Refresh Swagger**: Run `gen_api_template.py` in build environment (has proper DB access)
2. **Generate Template**: Create `api-gateway/template.yml` with ALL endpoints including:
   - `/api/organizations/{org_id}/dashboard`
   - `/api/organizations/{org_id}/sessions`
   - `/api/organizations/{org_id}/assignments`
   - `/api/organizations/{org_id}/branches`
   - `/api/organizations/{org_id}/branches/{branch_id}/terminals`
   - `/api/organizations/{org_id}/closings`
   - `/api/organizations/{org_id}/consecutives`
3. **Deploy API Gateway**: Update the deployed API Gateway with new endpoints and CORS config

### 4. Expected Result

After deployment:
- ✅ All new endpoints will be accessible
- ✅ CORS preflight will allow `x-user-id` header
- ✅ API Gateway will automatically inject `x-user-id` from Cognito JWT `sub` claim
- ✅ Frontend can successfully call all endpoints

### 5. Verification

After pipeline completes, test:
```bash
# Test CORS preflight
curl -X OPTIONS https://orders-api.jcampos.dev/api/organizations/{org_id}/dashboard \
  -H "Origin: http://localhost:9000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: authorization,x-user-id" \
  -v

# Should return:
# Access-Control-Allow-Headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,x-user-id
# Access-Control-Allow-Origin: *
```

### 6. Frontend Configuration

Frontend is already configured correctly:
- **pollos-sales**: `api.ts` conditionally sends `x-user-id` only to cross-app-be API
- **dashboard**: `queryClient.ts` conditionally sends `x-user-id` only to orders API
- Markets API does NOT receive `x-user-id` header (correct)

## Technical Details

### API Gateway Header Injection
```yaml
requestParameters:
  integration.request.header.x-user-id: context.authorizer.claims.sub
```

This configuration tells API Gateway to:
1. Extract the `sub` claim from the Cognito JWT token
2. Inject it as the `x-user-id` header before forwarding to Lambda
3. Backend receives the header without frontend needing to send it explicitly

### CORS Configuration
```yaml
Access-Control-Allow-Headers: 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,x-user-id'
Access-Control-Allow-Methods: 'GET,POST,PUT,PATCH,DELETE,OPTIONS'
Access-Control-Allow-Origin: '*'
```

This allows browsers to send the `x-user-id` header in cross-origin requests.

## Next Steps

1. Commit and push changes
2. Wait for pipeline to complete
3. Test frontend - CORS errors should be resolved
4. Verify all new endpoints are accessible
