# SKU Field Removal Summary

## Overview
Removed the standalone `sku` field from the Product model and DTOs. SKU values are now handled as code type 03 (MANUFACTURER) in the `codes` JSONB array, following the Hacienda e-invoicing standard.

## Rationale

The `sku` field was redundant because:
1. **Hacienda Standard**: Code type 03 is defined as "Código asignado por el fabricante" (Manufacturer code), which is essentially a SKU
2. **Consistency**: All product codes should be in the `codes` array for uniform handling
3. **Flexibility**: The codes array supports multiple code types without schema changes
4. **Simplification**: Reduces model complexity and eliminates duplicate data

## Changes Made

### 1. Database Migration
**File**: `alembic/versions/g7b8c9d0e1f2_remove_sku_column.py`

**Upgrade**:
- Migrates existing SKU values to `codes` array as type 03 (MANUFACTURER)
- Drops the `sku` column from products table

**Downgrade**:
- Adds `sku` column back
- Extracts code type 03 from `codes` array back to `sku` column

**Migration SQL**:
```sql
-- Migrate SKU to codes array
UPDATE products 
SET codes = COALESCE(codes, '[]'::jsonb) || jsonb_build_array(
    jsonb_build_object('codeTypeId', '03', 'number', sku)
)
WHERE sku IS NOT NULL AND sku != '';

-- Drop SKU column
ALTER TABLE products DROP COLUMN sku;
```

### 2. Product Model
**File**: `app/models/product.py`

**Removed**:
```python
sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
```

### 3. Product Request DTO
**File**: `app/dtos/requests/product_request_dto.py`

**Removed**:
```python
sku: Optional[str] = Field(None, alias="sku")
```

### 4. Product Service
**File**: `app/services/product_service.py`

**Removed from `create_product()`**:
```python
sku=dto.sku,
```

**Removed from `update_product()`**:
```python
if dto.sku is not None:
    product.sku = dto.sku
```

### 5. Fixed Duplicate Rows Issue
**File**: `app/repositories/product_repository.py`

**Added**:
- Detection of category joins in search filters
- Explicit JOIN with Category table when needed
- DISTINCT clause to prevent duplicate rows from joins

**Changes**:
```python
# Before: Implicit cross join causing duplicates
stmt = select(Product).where(base_filter)

# After: Explicit join with DISTINCT
if needs_category_join:
    stmt = (
        select(Product)
        .distinct()
        .join(Category, Product.category_id == Category.id)
        .where(base_filter)
    )
```

## Hacienda Code Types Reference

For reference, the Hacienda code types are:
- **01**: Código del producto del vendedor (Vendor/Seller code)
- **02**: Código del producto del comprador (Buyer code)
- **03**: Código asignado por el fabricante (Manufacturer code) - **This is SKU**
- **04**: Código uso interno (Internal code)
- **99**: Otros (Others)

## API Changes

### Before (SKU as separate field):
```json
{
  "name": "Product Name",
  "sku": "PROD-123",
  "codes": [
    {"codeTypeId": "01", "number": "VENDOR-456"}
  ]
}
```

### After (SKU in codes array):
```json
{
  "name": "Product Name",
  "codes": [
    {"codeTypeId": "01", "number": "VENDOR-456"},
    {"codeTypeId": "03", "number": "PROD-123"}
  ]
}
```

## Migration Steps

1. **Backup database** (recommended):
   ```bash
   pg_dump your_database > backup_before_sku_removal.sql
   ```

2. **Run migration**:
   ```bash
   alembic upgrade head
   ```

3. **Verify migration**:
   ```sql
   -- Check that SKU column is gone
   SELECT column_name FROM information_schema.columns 
   WHERE table_name = 'products' AND column_name = 'sku';
   -- Should return 0 rows
   
   -- Check that SKUs were migrated to codes
   SELECT id, name, codes 
   FROM products 
   WHERE codes @> '[{"codeTypeId": "03"}]'::jsonb
   LIMIT 10;
   ```

4. **Update frontend code**:
   - Remove `sku` field from product forms
   - Add SKU as code type 03 in the codes array
   - Update product display to show code type 03 as "SKU"

## Frontend Integration Guide

### Displaying SKU
```typescript
// Extract SKU from codes array
const sku = product.codes?.find(code => code.codeTypeId === '03')?.number;

// Display
<div>SKU: {sku || 'N/A'}</div>
```

### Setting SKU
```typescript
// When creating/updating product
const productData = {
  name: "Product Name",
  codes: [
    { codeTypeId: "03", number: skuValue }, // SKU
    { codeTypeId: "01", number: vendorCode },
    // ... other codes
  ]
};
```

### Form Validation
```typescript
// Validate SKU (code type 03) is unique
const hasSku = codes.some(code => code.codeTypeId === '03');
if (!hasSku) {
  errors.push('SKU (Manufacturer code) is required');
}
```

## Benefits

1. **Standards Compliance**: Aligns with Hacienda e-invoicing code type definitions
2. **Data Consistency**: All product codes in one place
3. **Reduced Redundancy**: Eliminates duplicate data storage
4. **Simplified Model**: Fewer fields to maintain
5. **Flexibility**: Easy to add/remove code types without schema changes
6. **Better Queries**: Can search across all code types uniformly

## Testing Checklist

- [ ] Run migration successfully
- [ ] Verify SKU column is dropped
- [ ] Verify existing SKUs migrated to codes array
- [ ] Create new product with code type 03
- [ ] Update product with code type 03
- [ ] Search products by code type 03
- [ ] Verify no duplicate rows in search results
- [ ] Test rollback migration (optional)

## Files Modified

- ✅ `alembic/versions/g7b8c9d0e1f2_remove_sku_column.py` (NEW)
- ✅ `app/models/product.py`
- ✅ `app/dtos/requests/product_request_dto.py`
- ✅ `app/services/product_service.py`
- ✅ `app/repositories/product_repository.py` (duplicate rows fix)
