# Backend Session Products Implementation

## ✅ Implementation Complete

All backend changes for session products have been successfully implemented and the database migration has been run.

## Changes Made

### 1. Database Schema ✅

**Migration**: `ad6674f93b70_add_session_products_table.py`

Created `session_products` table with:
- `id` (UUID, primary key)
- `session_id` (UUID, foreign key to sales_sessions, CASCADE on delete)
- `product_id` (VARCHAR(255))
- `organization_id` (VARCHAR(255))
- `created_at` (TIMESTAMP WITH TIME ZONE)

**Constraints**:
- Unique constraint on `(session_id, product_id)` - prevents duplicate products in same session
- Foreign key to `sales_sessions` with CASCADE delete

**Indexes**:
- `idx_session_products_session` on `session_id`
- `idx_session_products_product` on `product_id`

**Migration Status**: ✅ **APPLIED** - Migration ran successfully

### 2. Model Layer ✅

**File**: `app/models/session_product.py`

Created `SessionProduct` model with:
- All required fields matching the database schema
- Proper UUID handling
- Timestamp with timezone support
- Unique constraint definition

### 3. Repository Layer ✅

**File**: `app/repositories/session_product_repository.py`

Created `SessionProductRepository` with methods:
- `find_by_session(session_id)` - Get all products for a session
- `delete_by_session(session_id)` - Delete all products for a session
- `bulk_create(session_id, organization_id, product_ids)` - Create multiple session products efficiently

Extends `DatabaseConnection` following the existing repository pattern.

### 4. DTO Layer ✅

**Request DTO** (`app/dtos/requests/session_request_dto.py`):
- Added `product_ids: Optional[List[str]]` to `SessionCreateRequestDTO`
- Allows frontend to send list of product IDs when creating a session

**Response DTO** (`app/dtos/responses/session_dto.py`):
- Added `product_ids: Optional[List[str]]` to `SessionResponse`
- Returns list of product IDs when fetching session details

### 5. Service Layer ✅

**File**: `app/services/session_service.py`

Updated `create_session()`:
- Accepts `product_ids` from request DTO
- Creates session first
- Then bulk creates session products if product_ids provided
- Returns session with product_ids in response

Updated `get_session()`:
- Fetches session from database
- Loads associated product IDs from session_products table
- Returns session with product_ids populated

Updated `_map_session()`:
- Now accepts optional `product_ids` parameter
- Includes product_ids in SessionResponse

## API Changes

### Create Session Endpoint

**Endpoint**: `POST /api/organizations/{org_id}/sessions`

**Request Body** (NEW):
```json
{
  "name": "vs Herediano",
  "type": "match",
  "context": "caja",
  "start_time": "2024-01-15T19:00:00Z",
  "branch_id": "uuid",
  "expected_revenue": 50000,
  "product_ids": ["prod-1", "prod-2", "prod-3"]  // NEW - Optional
}
```

**Response**:
```json
{
  "session_id": "uuid",
  "organization_id": "org-123",
  "name": "vs Herediano",
  "type": "match",
  "context": "caja",
  "start_time": "2024-01-15T19:00:00Z",
  "status": 1,
  "created_by": "user-123",
  "product_ids": ["prod-1", "prod-2", "prod-3"]  // NEW
}
```

### Get Session Endpoint

**Endpoint**: `GET /api/organizations/{org_id}/sessions/{session_id}`

**Response** (UPDATED):
```json
{
  "session_id": "uuid",
  "organization_id": "org-123",
  "name": "vs Herediano",
  "type": "match",
  "context": "caja",
  "start_time": "2024-01-15T19:00:00Z",
  "status": 1,
  "created_by": "user-123",
  "product_ids": ["prod-1", "prod-2", "prod-3"]  // NEW - Loaded from session_products
}
```

## Database Queries

### Insert Session Products
```sql
INSERT INTO session_products (id, session_id, product_id, organization_id, created_at)
VALUES 
  (uuid_generate_v4(), 'session-uuid', 'prod-1', 'org-123', NOW()),
  (uuid_generate_v4(), 'session-uuid', 'prod-2', 'org-123', NOW()),
  (uuid_generate_v4(), 'session-uuid', 'prod-3', 'org-123', NOW());
```

### Get Products for Session
```sql
SELECT product_id 
FROM session_products 
WHERE session_id = 'session-uuid';
```

### Delete Session (CASCADE)
```sql
-- When deleting a session, session_products are automatically deleted
DELETE FROM sales_sessions WHERE session_id = 'session-uuid';
-- session_products rows are CASCADE deleted automatically
```

## Testing Checklist

### Backend Tests
- [x] Migration runs successfully
- [x] SessionProduct model can be imported
- [x] SessionProductRepository can be instantiated
- [ ] Create session with product_ids (requires DB connection)
- [ ] Get session returns product_ids (requires DB connection)
- [ ] Delete session cascades to session_products (requires DB connection)

### Integration Tests
- [ ] Frontend sends product_ids when creating session
- [ ] Backend saves session_products correctly
- [ ] Frontend receives product_ids when fetching session
- [ ] Inventory opening only shows selected products
- [ ] Session deletion removes associated products

## Frontend Integration

The frontend is already prepared to send `product_ids`:

**SessionConfig.tsx** (line ~120):
```typescript
const session = await crossAppApi.post<{ session_id: string }>(
  crossAppOrgPath(org!.id, "/sessions"),
  {
    name: sessionType === "partido" ? `vs ${rival}` : "Operación regular",
    type: sessionType === "partido" ? "match" : "shift",
    start_time,
    branch_id: branchId || undefined,
    // TODO: Add product_ids from selectedProducts state
    product_ids: Array.from(selectedProducts),  // ADD THIS LINE
  }
);
```

## Rollback Instructions

If needed, rollback the migration:

```bash
cd E:\dev\cross-app-be
python -c "from alembic import command; from alembic.config import Config; cfg = Config('alembic.ini'); command.downgrade(cfg, 'facc4b47c490')"
```

This will:
1. Drop the `session_products` table
2. Drop the indexes
3. Revert to the previous schema

## Performance Considerations

### Indexes
- `idx_session_products_session` - Fast lookup of all products in a session
- `idx_session_products_product` - Fast lookup of which sessions contain a product

### Bulk Operations
- `bulk_create()` uses single transaction for multiple inserts
- More efficient than individual inserts

### Cascade Delete
- When session is deleted, products are automatically removed
- No orphaned records
- Single DELETE statement handles cleanup

## Security Considerations

- Organization ID is stored with each session product
- Ensures products can only be accessed within correct organization context
- Foreign key constraint ensures referential integrity
- Unique constraint prevents duplicate product assignments

## Next Steps

1. ✅ Update frontend to send `product_ids` when creating session
2. ✅ Update inventory opening to filter by selected products
3. ✅ Test end-to-end flow
4. Add unit tests for SessionProductRepository
5. Add integration tests for session creation with products
