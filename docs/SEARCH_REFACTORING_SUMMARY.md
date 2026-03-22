# Search Filter Refactoring Summary

## Overview
Refactored the search filter system to use a common base class (`BaseSearchFilter`) that all entity-specific search filter enums inherit from. This ensures consistency, reduces code duplication, and fixes the `always_like` functionality.

## Changes Made

### 1. Created Base Search Filter Class
**File**: `app/enums/base_search_filter.py`

- Created `BaseSearchFilter` as a common base class for all search filter enums
- Contains all common properties and methods:
  - `entity_field`: Database field name
  - `json_field`: JSON request field name
  - `is_join_field`: Whether join is required
  - `join_field`: Relationship name for joins
  - `is_controller_filter`: Whether searchable in controllers
  - `allows_like`: Whether LIKE operations allowed
  - `allows_between`: Whether BETWEEN operations allowed
  - `sortable`: Whether field can be used for sorting
  - `always_like`: Whether to always use LIKE (even without wildcards)
- Includes `get_filter_by_json_field()` class method

### 2. Updated Search Filter Enums
**Files**: 
- `app/enums/search_filters.py` (Order filters)
- `app/enums/product_search_filters.py` (Product filters)

- Changed from inheriting `Enum` to inheriting `BaseSearchFilter`
- Removed duplicate `__init__` and property methods
- Removed duplicate `get_filter_by_json_field()` method
- Fixed `CATEGORY_NAME` definition in ProductSearchFilters:
  - Changed `join_field` from `"name"` to `"category"` (the relationship name)
  - Changed `entity_field` from `"category"` to `"name"` (the field in Category model)

### 3. Updated SearchUtils
**File**: `app/utils/search_utils.py`

- Updated imports to use `BaseSearchFilter` instead of `SearchFilters`
- Updated `SearchCriteria` dataclass:
  - Changed `search_filter` type to `Optional[BaseSearchFilter]`
  - Changed `filter_enum_class` type to `Type[BaseSearchFilter]`
  - Updated `__post_init__` to handle optional filter_enum_class
- Updated method signatures to use `Type[BaseSearchFilter]`:
  - `parse_search_filter()`
  - `_parse_criteria()`
  - `_parse_order_by()`
- Fixed join field handling to support newer SQLAlchemy versions:
  - Added fallback logic for accessing relationship mapper class
  - Handles both `relationship_attr.property.entity.class_` and `relationship_attr.property.mapper.class_`

## Bug Fixes

### 1. Always-Like Functionality
**Problem**: Fields marked with `always_like=True` (like `name`, `description`) were not using ILIKE even without wildcards.

**Root Cause**: The `filter_enum_class` was not being passed through to `SearchCriteria`, so it couldn't look up the filter properties.

**Solution**: 
- Added `filter_enum_class` parameter to `SearchCriteria`
- Pass it through from `parse_search_filter()` → `_parse_criteria()` → `SearchCriteria`
- `SearchCriteria.__post_init__()` now uses the correct enum class to look up filter properties

**Result**: 
- `name:Test` now generates `WHERE products.name ILIKE '%Test%'` ✓
- `name:*Test*` generates `WHERE products.name ILIKE '%Test%'` ✓

### 2. Join Field Handling
**Problem**: Join fields were failing with `AttributeError: mapper` in newer SQLAlchemy versions.

**Solution**: Added fallback logic in `_build_filter()` to handle different SQLAlchemy API versions:
```python
if hasattr(relationship_attr.property, 'entity'):
    current_class = relationship_attr.property.entity.class_
elif hasattr(relationship_attr.property, 'mapper'):
    current_class = relationship_attr.property.mapper.class_
```

### 3. Boolean Field Type Conversion
**Problem**: Searching `status:1` caused error: "operator does not exist: boolean = integer" because `is_active` is a boolean column but the value was being passed as integer.

**Root Cause**: The `_convert_value()` method converts `"1"` to integer `1`, but PostgreSQL doesn't allow comparing boolean columns with integers.

**Solution**: Added boolean type handling in `_apply_operation()`:
```python
# Handle BOOLEAN columns - convert integer values to boolean
elif "BOOLEAN" in col_type.upper():
    if isinstance(value, int):
        value = bool(value)
    elif isinstance(value, str):
        if value.lower() in ('1', 'true', 'yes', 'on'):
            value = True
        elif value.lower() in ('0', 'false', 'no', 'off'):
            value = False
```

**Result**:
- `status:1` generates `WHERE products.is_active = true` ✓
- `status:0` generates `WHERE products.is_active = false` ✓
- No more type mismatch errors ✓

## Test Results

All tests pass successfully:

### SQL Generation Tests
✓ Simple LIKE query generates `ILIKE '%value%'`
✓ Wildcard LIKE query generates `ILIKE '%value%'`
✓ BETWEEN query generates `>= AND <=`
✓ OR query generates proper `OR` logic
✓ Complex AND/OR queries work correctly
✓ Queries execute successfully against database
✓ Comparison operators (`>`, `<`) work correctly

### Always-Like Tests
✓ `name:Test` → `WHERE products.name ILIKE '%Test%'`
✓ `description:Professional` → Uses ILIKE with wildcards
✓ `categoryName:Beauty` → Join field with ILIKE works

### Boolean Field Tests
✓ `status:1` → `WHERE products.is_active = true`
✓ `status:0` → `WHERE products.is_active = false`
✓ Query executes successfully without type errors

### SQL Injection Safety
✓ All dangerous inputs are safely handled through parameterized queries

## Benefits

1. **Code Reusability**: Common functionality in one place
2. **Consistency**: All search filter enums have the same interface
3. **Type Safety**: SearchUtils now expects `BaseSearchFilter` type
4. **Maintainability**: Changes to base class automatically apply to all enums
5. **Extensibility**: Easy to add new entity-specific search filter enums
6. **Bug Fixes**: Always-like and join field handling now work correctly

## Migration Guide for Other Enums

To migrate other search filter enums (ClientSearchFilters, StoreSearchFilters, etc.):

1. Import `BaseSearchFilter`:
```python
from app.enums.base_search_filter import BaseSearchFilter
```

2. Change class declaration:
```python
# Before
class ClientSearchFilters(Enum):

# After
class ClientSearchFilters(BaseSearchFilter):
```

3. Remove duplicate code:
- Remove `__init__` method
- Remove all `@property` methods
- Remove `get_filter_by_json_field()` class method

4. Keep only the enum values:
```python
class ClientSearchFilters(BaseSearchFilter):
    NAME = ("name", "name", False, None, True, ENTITY_ALL, True, False, True, True)
    # ... other fields
```

## Files Modified

- ✅ `app/enums/base_search_filter.py` (NEW)
- ✅ `app/enums/search_filters.py`
- ✅ `app/enums/product_search_filters.py`
- ✅ `app/utils/search_utils.py`
- ✅ `test_search_fix.py` (enhanced with SQL validation tests)
- ✅ `test_always_like_debug.py` (NEW - debug test)

## Next Steps

1. Migrate remaining search filter enums:
   - `app/enums/client_search_filters.py`
   - `app/enums/store_search_filters.py`
   - `app/enums/department_search_filters.py`

2. Consider adding more test coverage for:
   - Nested joins (e.g., `terminal.branch`)
   - Edge cases with special characters
   - Performance testing with large datasets

3. Document the search filter system in API documentation
