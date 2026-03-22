# Client Unique Constraint & Deletion Logic - Implementation Summary

## Changes Overview

### 1. Unique Constraint Update
**Changed from**: `(company_id, client_gln)` unique  
**Changed to**: `(company_id, client_gln, nationality)` unique

This allows the same GLN to exist for different nationalities within the same organization.

### 2. Deletion & Reactivation Logic
- Deleted clients (status=3) **cannot** be updated via PUT or PATCH endpoints
- Deleted clients **can** be reactivated via POST endpoint
- POST endpoint checks for existing deleted client with same unique key and reactivates it

## Files Modified

### Model
**File**: `app/models/client.py`
- Updated `__table_args__` to use `idx_client_company_gln_nationality` instead of `idx_client_company_gln`

### Repository
**File**: `app/repositories/client_repository.py`
- Added `find_by_unique_key(company_id, client_gln, nationality)` method
  - Finds client by unique key including deleted ones (no status filter)

### Service
**File**: `app/services/client_service.py`

#### `create_client()`
```python
# New logic:
1. Check if deleted client exists with (company_id, client_gln, nationality)
2. If exists: Reactivate and update all fields, set status=1
3. If not exists: Create new client with status=1
```

#### `update_client()`
```python
# New validation:
if client.status == 3:
    raise ValueError("Cannot update deleted client. Use POST to reactivate.")
```

#### `update_client_status()`
```python
# New validation:
if client.status == 3:
    raise ValueError("Cannot update deleted client. Use POST to reactivate.")
```

### Controller
**File**: `app/controllers/clients_controller.py`
- Updated POST endpoint description: "Create a new client or reactivate deleted one"
- Updated PUT endpoint description: "Cannot update deleted clients (status=3). Use POST to reactivate."
- Updated PATCH endpoint description: "Cannot update deleted clients (status=3). Use POST to reactivate."

### Migrations
**File**: `alembic/versions/21de089670c4_update_client_unique_constraint.py`
- Drop old index: `idx_client_company_gln`
- Create new index: `idx_client_company_gln_nationality` on (company_id, client_gln, nationality)

## Workflow Examples

### Example 1: Create New Client
```
POST /api/organizations/org123/clients
{
  "clientGln": "1234567890123",
  "nationality": "CR",
  "clientName": "Test Client"
}

Result: New client created with status=1
```

### Example 2: Delete Client
```
PATCH /api/organizations/org123/clients/{client_id}
{
  "status": 3
}

Result: Client status updated to 3 (deleted), excluded from queries
```

### Example 3: Try to Update Deleted Client (FAILS)
```
PUT /api/organizations/org123/clients/{client_id}
{
  "clientName": "Updated Name"
}

Result: 400 Bad Request - "Cannot update deleted client. Use POST to reactivate."
```

### Example 4: Reactivate Deleted Client
```
POST /api/organizations/org123/clients
{
  "clientGln": "1234567890123",
  "nationality": "CR",
  "clientName": "Reactivated Client",
  "businessName": "New Business Name"
}

Result: 
- Finds deleted client with matching (company_id, client_gln, nationality)
- Reactivates with status=1
- Updates all fields with new data
- Returns same client_id
```

### Example 5: Try to Update Status of Deleted Client (FAILS)
```
PATCH /api/organizations/org123/clients/{client_id}
{
  "status": 1
}

Result: 400 Bad Request - "Cannot update deleted client. Use POST to reactivate."
```

## Database Migration

Run migrations to apply changes:
```bash
python3 -m alembic upgrade head
```

Or use db_push script:
```bash
python3 db_push.py
```

## Key Benefits

1. **Prevents Accidental Updates**: Deleted clients are protected from accidental modifications
2. **Clean Reactivation**: POST endpoint provides clear, intentional way to reactivate
3. **Data Integrity**: Unique constraint on (company_id, client_gln, nationality) prevents duplicates
4. **Audit Trail**: Same client_id is reused when reactivating, preserving relationships
5. **Flexible Nationality**: Same GLN can exist for different nationalities

## Error Handling

All ValueError exceptions from service layer are caught by controller and returned as:
- **400 Bad Request** for validation errors (e.g., trying to update deleted client)
- **404 Not Found** when client doesn't exist
- **422 Unprocessable Entity** for search filter errors
