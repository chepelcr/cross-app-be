# Client Status Implementation

## Overview
Added status management to clients with automatic status transitions and unique constraint enforcement. Deleted clients can be reactivated via POST endpoint.

## Unique Constraint
- **Unique Key**: (company_id, client_gln, nationality)
- Ensures no duplicate clients with same GLN and nationality within an organization
- Allows reactivation of deleted clients with same unique key

## Status Codes
- **0 (Pending)**: Client created automatically via order detail parsing (incomplete data)
- **1 (Active)**: Client created manually or updated with full information
- **2 (Inactive)**: Client manually deactivated
- **3 (Deleted)**: Client marked as deleted (soft delete, excluded from queries)

## Implementation Details

### 1. Database Changes
- Added `status` column to `clients` table (Integer, NOT NULL, default=0)
- Replaced unique index `idx_client_company_gln` with `idx_client_company_gln_nationality`
- Migration files:
  - `alembic/versions/bcede4283772_add_client_status.py`
  - `alembic/versions/21de089670c4_update_client_unique_constraint.py`

### 2. Model Changes
**File**: `app/models/client.py`
- Added `status: Mapped[int]` field with default value of 0

### 3. Repository Changes
**File**: `app/repositories/client_repository.py`
- `upsert()`: Sets `status=0` when creating new clients (for order detail parsing)
- `find_by_unique_key()`: New method to find client by (company_id, client_gln, nationality) including deleted
- All find methods now filter by `status.in_([0, 1, 2])` to exclude deleted clients (status=3)

### 4. Service Changes
**File**: `app/services/client_service.py`
- `create_client()`: Checks for deleted client with same unique key and reactivates if found, otherwise creates new with `status=1`
- `update_client()`: Prevents updating deleted clients (raises ValueError), auto-promotes pending to active
- `update_client_status()`: Prevents updating deleted clients (raises ValueError)
- `_map_client()`: Includes status in response mapping

### 5. DTO Changes
**File**: `app/dtos/responses/client_dto.py`
- Added `status: int` field to `ClientResponse`

### 6. Controller Changes
**File**: `app/controllers/clients_controller.py`
- POST endpoint: Updated to indicate it can reactivate deleted clients
- PUT endpoint: Updated to indicate deleted clients cannot be updated
- PATCH endpoint: Updated to indicate deleted clients cannot be updated

## Workflow

### Scenario 1: Client Created via Order Detail
1. Order Excel file is uploaded
2. Client is automatically created via `ClientRepository.upsert()`
3. Client is created with `status=0` (pending)
4. Client appears in listings but marked as pending

### Scenario 2: User Updates Pending Client
1. User calls PUT `/api/organizations/{org_id}/clients/{client_id}` with full client data
2. Service detects `status=0` and automatically promotes to `status=1` (active)
3. Client is now fully active

### Scenario 3: User Creates Client Manually
1. User calls POST `/api/organizations/{org_id}/clients` with client data
2. Client is created with `status=1` (active) immediately

### Scenario 4: User Deactivates Client
1. User calls PATCH `/api/organizations/{org_id}/clients/{client_id}` with `{"status": 2}`
2. Client status is updated to 2 (inactive)
3. Client still appears in queries but marked as inactive

### Scenario 5: User Deletes Client
1. User calls PATCH `/api/organizations/{org_id}/clients/{client_id}` with `{"status": 3}`
2. Client status is updated to 3 (deleted)
3. Client is excluded from all queries (soft delete)
4. Client cannot be updated via PUT or PATCH

### Scenario 6: User Reactivates Deleted Client
1. User calls POST `/api/organizations/{org_id}/clients` with same client_gln and nationality
2. Service finds deleted client with matching unique key
3. Client is reactivated with `status=1` and all fields updated
4. Same client_id is reused

## API Endpoints

### POST /api/organizations/{organization_id}/clients
Create a new client or reactivate deleted one.

**Request Body:**
```json
{
  "clientName": "Client Name",
  "clientGln": "1234567890123",
  "nationality": "CR",
  "businessName": "Business Name",
  "email": "email@example.com",
  "identification": {...},
  "phone": {...},
  "residence": {...}
}
```

**Behavior:**
- If no client exists with (company_id, client_gln, nationality): Creates new client with status=1
- If deleted client exists with same unique key: Reactivates and updates with new data

### PUT /api/organizations/{organization_id}/clients/{client_id}
Update an existing client. Returns 400 error if client is deleted.

### PATCH /api/organizations/{organization_id}/clients/{client_id}
Update client status. Returns 400 error if client is deleted.



## Migration Instructions

Run the migration to add the status column:
```bash
python3 -m alembic upgrade head
```

Or use the db_push script:
```bash
python3 db_push.py
```

## Notes
- Unique constraint on (company_id, client_gln, nationality) prevents duplicates
- Deleted clients (status=3) are excluded from all queries
- Deleted clients cannot be updated via PUT or PATCH - must use POST to reactivate
- POST endpoint intelligently reactivates deleted clients with same unique key
- Existing clients in database will get status=0 by default when migration runs
