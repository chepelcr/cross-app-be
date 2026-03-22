# Flat Code Columns Migration

## Overview

This migration removes the flat code columns (`internal_code`, `original_code`, `client_article_code`, `code`) from the `products` table and migrates all data to the JSONB `codes` array.

## What Changed

### Database Schema
- **Removed columns:**
  - `internal_code` (VARCHAR(50))
  - `original_code` (VARCHAR(50))
  - `client_article_code` (VARCHAR(50))
  - `code` (VARCHAR(50))
- **Removed index:** `idx_product_org_internal_code`
- **Kept:** `codes` JSONB array, `units_per_box`

### Code Changes

**1. Product Model (`app/models/product.py`):**
- Removed flat code column mappings
- Removed unique index on `internal_code`
- Updated docstring

**2. Product Repository (`app/repositories/product_repository.py`):**
- Removed `_build_codes_from_flat()` helper function
- Updated `find_by_company_and_internal_code()` to query JSONB array
- Updated `upsert_by_internal_code()` to build codes array directly
- Updated `find_all_by_company()` to remove internal_code filter
- Changed default ordering from `internal_code` to `name`

**3. Product Service (`app/services/product_service.py`):**
- Removed flat column assignments in `create_product()`
- Removed flat column updates in `update_product()`
- Updated `_map_product()` to extract flat codes from JSONB array for backward compatibility

**4. Orders Mapper (`app/mappers/orders_mapper.py`):**
- Added `_get_code_from_array()` helper function
- Updated `order_to_response()` to extract codes from JSONB array
- Updated `build_crossdocking_data()` to extract codes from JSONB array

**5. Search Filters (`app/enums/product_search_filters.py`):**
- Removed `INTERNAL_CODE` filter
- Kept `CODE` filter (queries JSONB array)

**6. API Controller (`app/controllers/products_controller.py`):**
- Updated documentation to remove `internalCode` search filter
- Updated sortable fields list

**7. API Documentation (`PRODUCTS_API.md`):**
- Updated search filters documentation
- Updated sortable fields
- Updated notes section to explain code storage

## Migration File

**Location:** `alembic/versions/d4e5f6a7b8c9_remove_flat_code_columns.py`

**What it does:**
1. Migrates existing flat column data to `codes` JSONB array
2. Drops the unique index on `internal_code`
3. Drops the flat code columns

**Downgrade:**
- Restores flat columns
- Extracts first code of each type from JSONB array back to flat columns
- Recreates unique index
- **Note:** This is a lossy downgrade - only the first code of each type is restored

## Running the Migration

### Prerequisites
1. Backup your database
2. Ensure all code changes are deployed
3. Test in a staging environment first

### Steps

1. **Check current migration status:**
   ```bash
   alembic current
   ```

2. **Run the migration:**
   ```bash
   alembic upgrade head
   ```

3. **Verify the migration:**
   ```sql
   -- Check that columns are removed
   \d products
   
   -- Check that codes array is populated
   SELECT id, codes FROM products LIMIT 10;
   
   -- Check that internal code lookup still works
   SELECT id, codes FROM products 
   WHERE codes @> '[{"codeTypeId": "04", "number": "YOUR_INTERNAL_CODE"}]';
   ```

4. **If rollback is needed:**
   ```bash
   alembic downgrade -1
   ```

## Backward Compatibility

The API maintains backward compatibility:

**Response Format:**
- API responses still include flat code fields (`internalCode`, `originalCode`, `clientArticleCode`, `code`)
- These are extracted from the JSONB `codes` array on-the-fly
- Existing API clients will continue to work without changes

**Request Format:**
- API requests should use the `codes` array
- Old flat fields in request DTOs are ignored (no longer mapped to model)

## Code Type Mapping

| Flat Column           | Code Type ID | Hacienda Name  |
|-----------------------|--------------|----------------|
| `internal_code`       | `04`         | Internal       |
| `original_code`       | `01`         | Vendor         |
| `client_article_code` | `02`         | Buyer          |
| `code`                | `03`         | Manufacturer   |

## Testing Checklist

- [ ] Products can be created with codes array
- [ ] Products can be updated with codes array
- [ ] Product lookup by internal code (type 04) works
- [ ] Product lookup by code type + number works
- [ ] Product search by code works (with and without type)
- [ ] Duplicate code validation works
- [ ] Order display shows correct product codes
- [ ] Cross-docking operations work correctly
- [ ] Excel order parsing creates products with codes
- [ ] API responses include flat code fields for backward compatibility

## Troubleshooting

**Issue:** Migration fails with "column does not exist"
- **Solution:** Ensure you're running the latest code version that doesn't reference flat columns

**Issue:** Products not found by internal code after migration
- **Solution:** Check that codes array is properly populated:
  ```sql
  SELECT id, codes FROM products WHERE codes IS NULL OR codes = '[]';
  ```

**Issue:** Duplicate code validation not working
- **Solution:** Verify the JSONB containment operator is working:
  ```sql
  SELECT id, codes FROM products 
  WHERE codes @> '[{"codeTypeId": "01", "number": "TEST123"}]';
  ```

## Performance Considerations

- JSONB queries use GIN indexes for optimal performance
- Consider adding a GIN index on the `codes` column if queries are slow:
  ```sql
  CREATE INDEX idx_products_codes_gin ON products USING GIN (codes);
  ```

## Support

If you encounter issues:
1. Check the migration logs
2. Verify database state with the SQL queries above
3. Review the code changes in this document
4. Test in a staging environment before production deployment
