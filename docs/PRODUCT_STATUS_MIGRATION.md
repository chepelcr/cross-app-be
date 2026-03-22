# Product Status Migration: is_active → status

## Overview
Migrated from boolean `is_active` column to integer `status` column to support three product states: Active, Inactive, and Deleted.

## Changes Summary

### 1. Created ProductStatus Enum
**File**: `app/enums/product_status.py`

```python
class ProductStatus(IntEnum):
    ACTIVE = 1      # Product is active and available
    INACTIVE = 2    # Product is inactive but not deleted
    DELETED = 3     # Product is soft-deleted
```

**Features**:
- `is_valid(status)`: Validate status values
- `get_valid_statuses()`: Get list of valid statuses
- `from_boolean(is_active)`: Convert boolean to status
- `to_boolean()`: Convert status to boolean (backward compatibility)
- `label` property: Human-readable status labels

### 2. Database Migration
**File**: `alembic/versions/f6a7b8c9d0e1_migrate_is_active_to_status.py`

**Upgrade Steps**:
1. Add `status` column (nullable)
2. Migrate data: `is_active=true` → `status=1`, `is_active=false` → `status=2`
3. Make `status` NOT NULL with default value 1
4. Drop `is_active` column
5. Add index on `status` column

**Downgrade Steps**:
- Reverses the migration back to `is_active` boolean

### 3. Updated Product Model
**File**: `app/models/product.py`

**Changes**:
- Replaced `is_active: Mapped[bool]` with `status: Mapped[int]`
- Added backward compatibility properties:
  ```python
  @property
  def is_active(self) -> bool:
      return self.status == ProductStatus.ACTIVE
  
  @is_active.setter
  def is_active(self, value: bool) -> None:
      self.status = ProductStatus.ACTIVE if value else ProductStatus.INACTIVE
  ```

### 4. Updated ProductSearchFilters
**File**: `app/enums/product_search_filters.py`

**Change**:
```python
# Before
STATUS = ("is_active", "status", False, None, True, ENTITY_ALL, False, False, False, False)

# After
STATUS = ("status", "status", False, None, True, ENTITY_ALL, False, False, False, False)
```

### 5. Updated Product Repository
**File**: `app/repositories/product_repository.py`

**Changes**:
- Replaced `Product.is_active == True` with `Product.status != ProductStatus.DELETED`
- This allows queries to return both ACTIVE and INACTIVE products, but not DELETED ones
- New products are created with `status=ProductStatus.ACTIVE`

**Query Behavior**:
- Default queries exclude DELETED products
- Frontend can filter by specific status values (1, 2, or 3)

### 6. Created ProductStatusRequestDTO
**File**: `app/dtos/requests/product_status_request_dto.py`

**Features**:
- Validates status is between 1-3
- Custom validator ensures status is valid using `ProductStatus.is_valid()`
- Clear error messages with valid status descriptions

### 7. Updated Products Controller
**File**: `app/controllers/products_controller.py`

**Changes**:
- Updated import to use `ProductStatusRequestDTO`
- Updated endpoint path to `/api/organizations/{organization_id}/products/{product_id}/status`
- Updated documentation to reflect new status values
- Added ValueError exception handling for invalid status

### 8. Updated Product Service
**File**: `app/services/product_service.py`

**Changes**:
- `update_product_status()` now validates status using `ProductStatus.is_valid()`
- Sets `product.status` directly instead of converting to boolean
- Raises `ValueError` for invalid status values with helpful message

### 9. Updated Search Utils
**File**: `app/utils/search_utils.py`

**Changes**:
- Removed BOOLEAN type handling
- Added INTEGER type handling for status column
- Converts boolean values to integers for backward compatibility (true→1, false→2)

## API Changes

### Update Product Status Endpoint

**Before**:
```
PATCH /api/organizations/{org_id}/products/{product_id}
Body: { "status": 1 }  // 1=active, 0=inactive
```

**After**:
```
PATCH /api/organizations/{org_id}/products/{product_id}/status
Body: { "status": 1 }  // 1=Active, 2=Inactive, 3=Deleted
```

### Search Filter Changes

**Before**:
```
GET /api/organizations/{org_id}/products?search=status:1  // 1=active, 0=inactive
```

**After**:
```
GET /api/organizations/{org_id}/products?search=status:1  // 1=Active
GET /api/organizations/{org_id}/products?search=status:2  // 2=Inactive
GET /api/organizations/{org_id}/products?search=status:3  // 3=Deleted
```

**Note**: Default queries (without status filter) return ACTIVE and INACTIVE products, but not DELETED.

## Migration Steps

1. **Run the migration**:
   ```bash
   alembic upgrade head
   ```

2. **Verify data migration**:
   ```sql
   SELECT status, COUNT(*) FROM products GROUP BY status;
   ```
   Expected: All products should have status 1 or 2

3. **Test the API**:
   - Test updating product status to 1, 2, and 3
   - Test searching by status
   - Verify deleted products (status=3) don't appear in default queries

## Backward Compatibility

The `Product` model includes backward compatibility properties:
- `product.is_active` getter returns `True` if status is ACTIVE
- `product.is_active` setter converts boolean to status (True→1, False→2)

This allows existing code that uses `is_active` to continue working without changes.

## Benefits

1. **Three States**: Can now distinguish between inactive and deleted products
2. **Soft Delete**: Products can be marked as deleted without removing from database
3. **Better Reporting**: Can track product lifecycle (active → inactive → deleted)
4. **Extensible**: Easy to add more status values in the future if needed
5. **Type Safety**: Integer enum is more explicit than boolean

## Testing

Test the following scenarios:
1. Create new product (should have status=1)
2. Update product status to 2 (inactive)
3. Update product status to 3 (deleted)
4. Search for products with status:1
5. Search for products with status:2
6. Verify deleted products (status:3) don't appear in default list
7. Try invalid status values (should return 400 error)

## Files Modified

- ✅ `app/enums/product_status.py` (NEW)
- ✅ `alembic/versions/f6a7b8c9d0e1_migrate_is_active_to_status.py` (NEW)
- ✅ `app/models/product.py`
- ✅ `app/enums/product_search_filters.py`
- ✅ `app/repositories/product_repository.py`
- ✅ `app/dtos/requests/product_status_request_dto.py` (NEW)
- ✅ `app/controllers/products_controller.py`
- ✅ `app/services/product_service.py`
- ✅ `app/utils/search_utils.py`
