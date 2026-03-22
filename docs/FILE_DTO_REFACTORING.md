# File DTO Refactoring Summary

## Overview

Refactored duplicated file DTOs across the codebase into a common `app/dtos/files` package with a base `FileDTO` class and specialized subclasses.

## New Package Structure

```
app/dtos/files/
├── __init__.py
├── file_dto.py          # Base class for all file uploads
├── image_dto.py         # For image uploads (PNG, JPEG, GIF, WEBP)
├── excel_dto.py         # For Excel file uploads
└── excel_and_color_dto.py  # Excel with color scheme (for reports)
```

## Class Hierarchy

```
FileDTO (base)
├── ImageDTO
│   └── Used by: products, categories
├── ExcelDTO
│   └── Used by: products, orders, stores
└── ExcelAndColorDTO
    └── Used by: crossdocking orders (parse endpoint)
```

## Base FileDTO

```python
class FileDTO(BaseModel):
    """Base DTO for file uploads with base64-encoded data."""
    
    data: str                    # Base64-encoded file data
    name: Optional[str]          # Filename (e.g., file.ext)
    content_type: str            # MIME type (e.g., image/png)
```

## Specialized DTOs

### ImageDTO
- Extends `FileDTO`
- Used for image uploads in products and categories
- Supports: PNG, JPEG, GIF, WEBP
- Max size: 5MB

### ExcelDTO
- Extends `FileDTO`
- Used for Excel file uploads
- Default content_type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Used in: product imports, order processing, store uploads

### ExcelAndColorDTO
- Extends `ExcelDTO`
- Adds optional `color` field for report generation
- Used directly in: crossdocking order parse endpoint
- Color schemes: green, orange, blue, green_alt

## Migration Changes

### Files Modified

1. **New Files Created:**
   - `app/dtos/files/file_dto.py`
   - `app/dtos/files/image_dto.py`
   - `app/dtos/files/excel_dto.py`
   - `app/dtos/files/excel_and_color_dto.py`
   - `app/dtos/files/__init__.py`

2. **Files Deleted:**
   - `app/dtos/requests/excel_file_dto.py` (replaced by ExcelDTO)

3. **Files Updated:**

   **Request DTOs:**
   - `app/dtos/requests/category_request_dto.py` - Removed duplicate ImageDTO, imports from files package
   - `app/dtos/requests/product_request_dto.py` - Removed duplicate ImageDTO, imports from files package
   - `app/dtos/requests/crossdocking_request_dto.py` - Renamed to `select_color_dto.py`, removed CrossdockingParseRequestDTO wrapper
   - `app/dtos/requests/__init__.py` - Updated exports
   - `app/dtos/__init__.py` - Updated imports and exports

   **Services:**
   - `app/services/category_service.py` - Updated ImageDTO import
   - `app/services/product_service.py` - Updated ImageDTO import
   - `app/services/product_excel_service.py` - Updated to use ExcelDTO
   - `app/services/order_service.py` - Updated to use ExcelDTO and CrossdockingParseRequestDTO
   - `app/services/store_service.py` - Updated to use ExcelDTO

   **Controllers:**
   - `app/controllers/categories_controller.py` - No changes needed (uses CategoryRequestDTO)
   - `app/controllers/products_controller.py` - Updated to use ExcelDTO
   - `app/controllers/orders_controller.py` - Updated to use ExcelDTO
   - `app/controllers/stores_controller.py` - Updated to use ExcelDTO

   **Utils:**
   - `app/utils/crossdocking_utils.py` - Updated to use ExcelDTO

   **Tests:**
   - `test_product_excel_import.py` - Updated to use ExcelDTO

## Benefits

1. **DRY Principle**: Eliminated duplicate ImageDTO and ExcelFileDTO definitions
2. **Maintainability**: Single source of truth for file upload DTOs
3. **Extensibility**: Easy to add new file types by extending FileDTO
4. **Type Safety**: Clear inheritance hierarchy with proper typing, removed unsafe `getattr()` calls
5. **Consistency**: All file uploads follow the same pattern
6. **Simplicity**: Removed unnecessary wrapper classes (CrossdockingParseRequestDTO)

## Usage Examples

### Image Upload (Products/Categories)

```python
from app.dtos.files import ImageDTO

image = ImageDTO(
    data="base64-encoded-data",
    name="product.png",
    contentType="image/png"
)
```

### Excel Upload (Products/Orders/Stores)

```python
from app.dtos.files import ExcelDTO

excel = ExcelDTO(
    data="base64-encoded-data",
    name="products",
    contentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
```

### Excel with Color (Crossdocking)

```python
from app.dtos.files import ExcelAndColorDTO
from app.enums.report_color import ReportColorScheme

excel = ExcelAndColorDTO(
    data="base64-encoded-data",
    name="crossdocking",
    contentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    color=ReportColorScheme.GREEN
)
```

## Import Paths

**Old:**
```python
from app.dtos.requests.product_request_dto import ImageDTO
from app.dtos.requests.category_request_dto import ImageDTO
from app.dtos.requests.excel_file_dto import ExcelFileDTO
```

**New:**
```python
from app.dtos.files import ImageDTO, ExcelDTO, ExcelAndColorDTO
```

## Backward Compatibility

- All existing API endpoints remain unchanged
- Request/response formats are identical
- Only internal implementation changed
- No breaking changes for frontend

## Testing

All existing tests pass without modification (except import updates):
- Product Excel import tests
- Category image upload tests
- Order processing tests
- Store upload tests

## Future Enhancements

Potential additions to the files package:
- `PdfDTO` - For PDF uploads
- `CsvDTO` - For CSV file uploads
- `VideoDTO` - For video uploads
- `DocumentDTO` - For general document uploads (Word, etc.)

All would extend the base `FileDTO` class for consistency.


## Code Quality Improvements

### Removed getattr() Calls

Replaced unsafe `getattr()` calls with direct property access for better type safety in services and DTOs.

**Audit Results:**
- ✅ Removed 3 problematic instances from `app/services/order_service.py`
- ✅ 0 instances in controllers, DTOs, repositories, mappers
- ✅ 5 legitimate instances remain in `app/utils/search_utils.py` (dynamic SQLAlchemy reflection)

**Before:**
```python
color = getattr(body, "color", None) or _default_color_for_order(order)
supplier_name = getattr(parsed, "supplier_name", None) or ""
```

**After:**
```python
color = body.color or _default_color_for_order(order)
supplier_name = parsed.supplier_name if hasattr(parsed, "supplier_name") else ""
```

**Benefits:**
- Type safety and IDE autocomplete
- Clearer intent and better error messages
- Proper typing for DTOs and known structures

See `GETATTR_AUDIT.md` for complete audit details.

### Removed Unnecessary Wrapper Classes

**Before:**
```python
class CrossdockingParseRequestDTO(ExcelAndColorDTO):
    """Request body for parsing a crossdocking Excel file with optional color scheme."""
    pass  # Empty wrapper, adds nothing!
```

**After:**
```python
# Use ExcelAndColorDTO directly in controllers and services
async def parse_and_save_crossdocking(
    body: ExcelAndColorDTO = Body(...),
):
```

This eliminates unnecessary abstraction layers and makes the code more straightforward.
