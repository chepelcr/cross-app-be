# Test Migration Guide

## Overview
This guide explains how to update integration tests after the API refactoring that moved user ID from path parameter to header.

## Changes Required in Tests

### 1. Update URL Patterns

**Before:**
```python
response = client.get(
    f"/api/users/{user_id}/organization/{org_id}/branches"
)
```

**After:**
```python
response = client.get(
    f"/api/organization/{org_id}/branches",
    headers={"x-user-id": user_id}
)
```

### 2. Add Headers to All Requests

All HTTP methods (GET, POST, PATCH, DELETE) now require the `x-user-id` header:

```python
# GET request
response = client.get(
    f"/api/organization/{org_id}/branches",
    headers={"x-user-id": user_id}
)

# POST request
response = client.post(
    f"/api/organization/{org_id}/branches",
    headers={"x-user-id": user_id},
    json={"name": "Branch 1", "code": "B1", "type": "stand"}
)

# PATCH request
response = client.patch(
    f"/api/organization/{org_id}/branches/{branch_id}",
    headers={"x-user-id": user_id},
    json={"name": "Updated Branch"}
)

# DELETE request
response = client.delete(
    f"/api/organization/{org_id}/branches/{branch_id}",
    headers={"x-user-id": user_id}
)
```

## Affected Test Files

The following test files need to be updated:

1. `tests/test_assignments_integration.py`
2. `tests/test_branches_integration.py` (if exists)
3. `tests/test_closings_integration.py` (if exists)
4. `tests/test_consecutives_integration.py` (if exists)
5. `tests/test_dashboard_integration.py`
6. `tests/test_sessions_integration.py` (if exists)
7. `tests/test_terminals_integration.py` (if exists)

## Example: Complete Test Update

### Before
```python
def test_list_branches(client, setup_test_data):
    user_id, org_id, branch = setup_test_data
    
    response = client.get(
        f"/api/users/{user_id}/organization/{org_id}/branches"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
```

### After
```python
def test_list_branches(client, setup_test_data):
    user_id, org_id, branch = setup_test_data
    
    response = client.get(
        f"/api/organization/{org_id}/branches",
        headers={"x-user-id": user_id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
```

## Helper Function (Optional)

You can create a helper function to simplify test code:

```python
def make_request(client, method: str, url: str, user_id: str, **kwargs):
    """Helper function to make requests with x-user-id header."""
    headers = kwargs.pop("headers", {})
    headers["x-user-id"] = user_id
    
    method_func = getattr(client, method.lower())
    return method_func(url, headers=headers, **kwargs)

# Usage
response = make_request(
    client, "GET", 
    f"/api/organization/{org_id}/branches",
    user_id
)

response = make_request(
    client, "POST",
    f"/api/organization/{org_id}/branches",
    user_id,
    json={"name": "Branch 1", "code": "B1", "type": "stand"}
)
```

## Automated Migration Script

You can use the following regex patterns to help with migration:

### Pattern 1: Simple GET requests
**Find:**
```regex
client\.get\(\s*f"/api/users/\{user_id\}/organization/\{([^}]+)\}/([^"]+)"\s*\)
```

**Replace:**
```
client.get(f"/api/organization/{$1}/$2", headers={"x-user-id": user_id})
```

### Pattern 2: POST/PATCH/DELETE with json
**Find:**
```regex
client\.(post|patch|delete)\(\s*f"/api/users/\{user_id\}/organization/\{([^}]+)\}/([^"]+)",\s*json=
```

**Replace:**
```
client.$1(f"/api/organization/{$2}/$3", headers={"x-user-id": user_id}, json=
```

## Testing Checklist

- [ ] Update all URL patterns to remove `/users/{user_id}`
- [ ] Add `x-user-id` header to all requests
- [ ] Run all integration tests
- [ ] Verify all tests pass
- [ ] Check for any hardcoded URLs in test fixtures
- [ ] Update any test documentation

## Notes

- The `x-user-id` header is case-insensitive in HTTP, but FastAPI expects it as `x-user-id` (lowercase with hyphens)
- Make sure to pass the header in all requests, including those in setup/teardown functions
- If using authentication in tests, ensure the header is added after authentication headers
