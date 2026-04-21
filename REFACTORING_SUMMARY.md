# API Refactoring Summary: User ID from Path to Header

## Overview
Refactored all API endpoints to receive the user ID via the `x-user-id` header instead of as a path parameter `/users/{user_id}`.

## Changes Made

### Route Pattern Changes
**Before:**
```
/api/users/{user_id}/organization/{organization_id}/{resource}
```

**After:**
```
/api/organization/{organization_id}/{resource}
```

### Parameter Changes
**Before:**
```python
async def endpoint(
    user_id: Annotated[str, Path(description="User identifier")],
    organization_id: Annotated[str, Path(description="Organization identifier")],
    ...
):
```

**After:**
```python
async def endpoint(
    organization_id: Annotated[str, Path(description="Organization identifier")],
    x_user_id: Annotated[str, Header(description="User identifier from header")],
    ...
):
```

## Affected Controllers

The following controllers were refactored:

1. **assignments_controller.py** - All assignment endpoints
2. **branches_controller.py** - All branch endpoints
3. **closings_controller.py** - All closing endpoints
4. **consecutives_controller.py** - All consecutive endpoints
5. **dashboard_controller.py** - Dashboard endpoint
6. **sessions_controller.py** - All session endpoints
7. **terminals_controller.py** - All terminal endpoints

## Endpoints Updated

### Assignments
- `GET /api/organization/{organization_id}/assignments`
- `GET /api/organization/{organization_id}/assignments/{assignment_id}`
- `POST /api/organization/{organization_id}/assignments`
- `PATCH /api/organization/{organization_id}/assignments/{assignment_id}`
- `PATCH /api/organization/{organization_id}/assignments/{assignment_id}/status`
- `DELETE /api/organization/{organization_id}/assignments/{assignment_id}`

### Branches
- `GET /api/organization/{organization_id}/branches`
- `GET /api/organization/{organization_id}/branches/{branch_id}`
- `POST /api/organization/{organization_id}/branches`
- `PATCH /api/organization/{organization_id}/branches/{branch_id}`
- `PATCH /api/organization/{organization_id}/branches/{branch_id}/status`
- `DELETE /api/organization/{organization_id}/branches/{branch_id}`

### Closings
- `GET /api/organization/{organization_id}/closings`
- `GET /api/organization/{organization_id}/closings/{closing_id}`
- `POST /api/organization/{organization_id}/closings`
- `PATCH /api/organization/{organization_id}/closings/{closing_id}`
- `PATCH /api/organization/{organization_id}/closings/{closing_id}/status`
- `DELETE /api/organization/{organization_id}/closings/{closing_id}`

### Consecutives
- `GET /api/organization/{organization_id}/consecutives`
- `GET /api/organization/{organization_id}/consecutives/{consecutive_id}`
- `GET /api/organization/{organization_id}/terminals/{terminal_id}/consecutives/{document_type_id}`
- `POST /api/organization/{organization_id}/consecutives`
- `PATCH /api/organization/{organization_id}/consecutives/{consecutive_id}/status`

### Dashboard
- `GET /api/organization/{organization_id}/dashboard`

### Sessions
- `GET /api/organization/{organization_id}/sessions`
- `GET /api/organization/{organization_id}/sessions/{session_id}`
- `POST /api/organization/{organization_id}/sessions`
- `PATCH /api/organization/{organization_id}/sessions/{session_id}`
- `PATCH /api/organization/{organization_id}/sessions/{session_id}/status`
- `DELETE /api/organization/{organization_id}/sessions/{session_id}`

### Terminals
- `GET /api/organization/{organization_id}/terminals`
- `GET /api/organization/{organization_id}/terminals/{terminal_id}`
- `POST /api/organization/{organization_id}/terminals`
- `PATCH /api/organization/{organization_id}/terminals/{terminal_id}`
- `PATCH /api/organization/{organization_id}/terminals/{terminal_id}/status`
- `DELETE /api/organization/{organization_id}/terminals/{terminal_id}`

## Breaking Changes

⚠️ **This is a breaking change for API clients!**

All clients consuming these endpoints must:

1. **Remove** the `/users/{user_id}` segment from the URL path
2. **Add** the `x-user-id` header to all requests

### Example Migration

**Before:**
```bash
curl -X GET "https://api.example.com/api/users/user123/organization/org456/branches" \
  -H "Authorization: Bearer token"
```

**After:**
```bash
curl -X GET "https://api.example.com/api/organization/org456/branches" \
  -H "Authorization: Bearer token" \
  -H "x-user-id: user123"
```

## Next Steps

1. **Update API Gateway** - Configure the API Gateway to extract the user ID from the JWT token and inject it as the `x-user-id` header
2. **Update Tests** - Update integration tests to use the new URL pattern and header
3. **Update Documentation** - Update OpenAPI/Swagger documentation
4. **Update Frontend** - Update all frontend API calls to use the new pattern
5. **Update Mobile Apps** - Update all mobile app API calls to use the new pattern

## Benefits

1. **Cleaner URLs** - Shorter, more semantic URLs
2. **Better Security** - User ID comes from authenticated header, not URL
3. **Consistency** - Aligns with standard practice of passing user context via headers
4. **API Gateway Integration** - Easier to inject user ID from JWT at the gateway level
