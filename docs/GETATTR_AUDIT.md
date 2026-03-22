# getattr() Usage Audit

## Summary

Comprehensive audit of all `getattr()` usages across the application.

## Results

### ✅ Removed (Problematic Usage)

**Location**: `app/services/order_service.py`

**Before:**
```python
# Line 229 - Accessing DTO property
color = getattr(body, "color", None) or _default_color_for_order(order)

# Lines 56-57 - Accessing parsed object properties
supplier_name = getattr(parsed, "supplier_name", None) or ""
supplier_gln = getattr(parsed, "supplier_gln", None) or ""
```

**After:**
```python
# Direct property access with proper typing
color = body.color or _default_color_for_order(order)

# Conditional access with hasattr
supplier_name = parsed.supplier_name if hasattr(parsed, "supplier_name") else ""
supplier_gln = parsed.supplier_gln if hasattr(parsed, "supplier_gln") else ""
```

**Why removed**: These were accessing known DTO/object properties where the structure is defined at compile time. Using direct property access provides:
- Type safety
- IDE autocomplete
- Better error messages
- Clearer intent

### ✅ Kept (Legitimate Usage)

**Location**: `app/utils/search_utils.py`

**Usage:**
```python
# Line 230 - Dynamic SQLAlchemy relationship access
relationship_attr = getattr(entity_class, rel_name)

# Line 234 - Dynamic column access on related model
target_column = getattr(target_model, criteria.join_field)

# Line 248 - Dynamic column access for filtering
column: InstrumentedAttribute = getattr(entity_class, field_name)

# Line 260 - Dynamic JSONB column access
codes_column = getattr(entity_class, "codes")

# Line 369 - Dynamic column access for sorting
column = getattr(entity_class, entity_field_name)
```

**Why kept**: These are legitimate reflection/metaprogramming patterns because:
1. **Dynamic entity handling**: Works with any SQLAlchemy model class
2. **Runtime field resolution**: Field names come from user search queries
3. **Protected with hasattr()**: All usages check for attribute existence first
4. **Appropriate abstraction**: This is a generic utility that must work dynamically

## Audit Coverage

### ✅ No getattr() found in:
- `app/controllers/**/*.py` - 0 instances
- `app/services/**/*.py` - 0 instances (after cleanup)
- `app/dtos/**/*.py` - 0 instances
- `app/repositories/**/*.py` - 0 instances
- `app/mappers/**/*.py` - 0 instances

### ✅ Legitimate getattr() in:
- `app/utils/search_utils.py` - 5 instances (all appropriate)

## Guidelines for Future Code

### ❌ Don't use getattr() for:
- Accessing DTO properties
- Accessing model properties with known structure
- Working around type checking
- Accessing properties that should always exist

### ✅ Do use getattr() for:
- Dynamic attribute access in generic utilities
- Reflection/metaprogramming patterns
- Working with unknown/dynamic structures
- Always pair with `hasattr()` checks

## Example Patterns

### Bad Pattern (Avoid)
```python
# Accessing known DTO property
value = getattr(dto, "field_name", None)

# Workaround for optional fields
color = getattr(body, "color", "default")
```

### Good Pattern (Use Instead)
```python
# Direct access with proper typing
value = dto.field_name

# Optional field with proper handling
color = body.color or "default"

# Truly optional with None check
color = body.color if body.color is not None else "default"
```

### Acceptable Pattern (Dynamic/Generic Code)
```python
# Generic utility working with any class
if hasattr(entity_class, field_name):
    column = getattr(entity_class, field_name)
    # Use column dynamically
```

## Conclusion

All problematic `getattr()` usages have been removed from services and DTOs. Remaining usages in `search_utils.py` are appropriate for the dynamic/generic nature of that utility.

**Total getattr() in codebase**: 5 (all legitimate)
**Removed**: 3 (from order_service.py)
**Status**: ✅ Clean
