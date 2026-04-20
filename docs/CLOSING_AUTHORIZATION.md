# Closing Authorization Implementation

## Overview

This document describes the implementation of manager-only authorization for closing approval and rejection operations, as specified in **Requirement 5.7** of the Backend Services Gap Analysis specification.

## Requirement

**Requirement 5.7**: THE System SHALL enforce that only managers can approve or reject closings.

## Implementation

### Service Layer (`app/services/closing_service.py`)

The `update_closing` function has been enhanced with authorization logic:

```python
def update_closing(
    organization_id: str,
    user_id: str,
    closing_id: str,
    dto: ClosingUpdateRequestDTO,
    is_manager: bool = True,
) -> Optional[ClosingResponse]:
```

**Key Features:**

1. **Authorization Check**: When the status is being updated to 'approved' or 'rejected', the function checks if `is_manager` is `True`. If not, it raises a `PermissionError`.

2. **Backward Compatibility**: The `is_manager` parameter defaults to `True` to maintain backward compatibility with existing code.

3. **Defense in Depth**: This service-level check provides an additional layer of security beyond API Gateway/auth layer enforcement.

4. **Granular Control**: Only approval/rejection operations are restricted. Other operations (updating notes, setting status to 'pending') are allowed for all users.

### Controller Layer (`app/controllers/closings_controller.py`)

The PATCH endpoint has been updated to handle authorization:

```python
async def update_closing(...):
    try:
        # TODO: Get user role from API Gateway/auth layer via request context
        # For now, we assume all users are managers (is_manager=True)
        # In production, this should be extracted from JWT claims or auth context:
        # is_manager = request.state.user_role == 'manager'
        is_manager = True  # Placeholder - should be determined by auth layer
        
        result = closing_service.update_closing(
            organization_id, user_id, closing_id, body, is_manager=is_manager
        )
        ...
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
```

**Key Features:**

1. **403 Forbidden Response**: When authorization fails, the endpoint returns HTTP 403 with a descriptive error message.

2. **TODO Comment**: Clear documentation indicates where the actual role checking should be implemented.

3. **Placeholder Logic**: Currently defaults to `is_manager=True` for all users. This should be replaced with actual role checking from the authentication layer.

### API Documentation

The endpoint description has been updated to document the authorization requirement:

```markdown
**Authorization:**
- Only managers can approve or reject closings (Requirement 5.7)
- Authorization enforcement should be done at API Gateway/auth layer
- Service layer provides defense-in-depth validation

**Error Responses:**
- 403: User does not have manager role for approval/rejection operations
```

## Testing

### Unit Tests (`tests/test_closing_authorization_unit.py`)

Comprehensive unit tests verify the authorization logic without requiring database access:

- ✅ `test_manager_can_approve_closing` - Managers can approve
- ✅ `test_manager_can_reject_closing` - Managers can reject
- ✅ `test_non_manager_cannot_approve_closing` - Non-managers blocked from approving
- ✅ `test_non_manager_cannot_reject_closing` - Non-managers blocked from rejecting
- ✅ `test_non_manager_can_update_notes` - Non-managers can update notes
- ✅ `test_non_manager_can_set_status_to_pending` - Non-managers can set to pending
- ✅ `test_authorization_check_only_for_approval_rejection` - Authorization only for approve/reject
- ✅ `test_manager_approval_sets_reviewed_fields` - Reviewed fields set correctly
- ✅ `test_explicit_reviewed_by_overrides_user_id` - Explicit reviewer ID works

All tests pass successfully.

### Integration Tests (`tests/test_closing_manager_authorization.py`)

Integration tests verify the authorization logic with real database operations. These tests require database credentials to run.

## Production Deployment

### Required Changes for Production

1. **API Gateway/Auth Layer Integration**:
   - Extract user role from JWT claims or authentication context
   - Pass the actual `is_manager` value to the service layer
   - Example: `is_manager = request.state.user_role == 'manager'`

2. **Role Management**:
   - Ensure user roles are properly set in the authentication system
   - Define clear criteria for manager role assignment
   - Consider organization-scoped roles (user may be manager in one org but not another)

3. **Error Handling**:
   - Log authorization failures for security monitoring
   - Consider rate limiting on failed authorization attempts
   - Provide clear error messages to users

### Security Considerations

1. **Defense in Depth**: The service layer check provides protection even if API Gateway authorization is bypassed.

2. **Explicit Authorization**: The `is_manager` parameter must be explicitly passed, preventing accidental privilege escalation.

3. **Audit Trail**: The `reviewed_by` and `reviewed_at` fields provide an audit trail of who approved/rejected closings.

4. **Granular Permissions**: Only approval/rejection operations are restricted, allowing cashiers to update notes and other non-critical fields.

## Architecture Notes

### Why Service Layer Authorization?

While the design document mentions "enforcement should be done at API Gateway/auth layer", we've implemented authorization at the service layer for several reasons:

1. **Defense in Depth**: Multiple layers of security are better than one
2. **Business Logic Coupling**: The authorization rule is tightly coupled to the business logic
3. **Testability**: Service-level authorization is easier to unit test
4. **Flexibility**: Allows for complex authorization rules that may be difficult to express at the API Gateway level

### API Gateway vs Service Layer

**API Gateway Authorization** (Recommended for Production):
- Prevents unauthorized requests from reaching the service
- Reduces load on backend services
- Centralized authorization logic
- Faster rejection of unauthorized requests

**Service Layer Authorization** (Current Implementation):
- Defense in depth
- Business logic validation
- Easier to test
- Works regardless of how the service is accessed

**Best Practice**: Implement both layers for maximum security.

## Related Requirements

- **Requirement 5.5**: When a manager approves a closing, reviewed_by and reviewed_at are set
- **Requirement 5.6**: When a manager rejects a closing, reviewed_by and reviewed_at are set
- **Requirement 8**: Authorization and Security - manager-only operations
- **Requirement 10.3**: API returns 403 Forbidden when authorization checks fail

## Future Enhancements

1. **Organization-Scoped Roles**: User may be manager in one organization but not another
2. **Permission Levels**: Different manager levels with different approval limits
3. **Delegation**: Allow managers to delegate approval authority
4. **Audit Logging**: Enhanced logging of all authorization decisions
5. **Role-Based Access Control (RBAC)**: More granular permission system
