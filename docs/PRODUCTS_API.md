# Products API

## Base URL
`/api/organizations/{organization_id}/products`

## Endpoints

### 1. List Products
**GET** `/api/organizations/{organization_id}/products`

Get paginated list of products with optional search filters.

**Query Parameters:**
- `page` (integer, optional): Page number (1-indexed). Default: 1
- `pageSize` (integer, optional): Items per page (1-100). Default: 12
- `search` (string, optional): Search filter string

**Search Filters:**
- `description`: Product description (supports wildcards)
- `code`: Product code lookup in codes JSONB array
  - Format with code type: `code:01-123415` (searches for codeTypeId "01" and number "123415")
  - Format without code type: `code:123415` (searches all code types for number "123415")
- `name`: Product name (supports wildcards)
- `categoryId`: Filter by category ID (exact match)
- `categoryName`: Filter by category name (supports wildcards)
- `status`: Filter by active status (1 = active, 0 = inactive)
- `price`: Filter by net price (supports between, greater than, less than)
  - Single value: `price:100` (exact match)
  - Range: `price:50~150` (between 50 and 150)
  - Greater than: `price>100`
  - Less than: `price<100`
- `salePrice`: Filter by sale price (supports between, greater than, less than)
  - Single value: `salePrice:100` (exact match)
  - Range: `salePrice:50~150` (between 50 and 150)
  - Greater than: `salePrice>100`
  - Less than: `salePrice<100`
- `createdOn`: Product creation timestamp
- `updatedOn`: Product last update timestamp

**Sorting:**
- `orderBy>field` (Ascending)
- `orderBy<field` (Descending)
- Sortable fields: `description`, `name`, `price`, `salePrice`, `createdOn`, `updatedOn`

**Examples:**
- `?search=name:*shampoo*,orderBy>name` - Products with "shampoo" in name, sorted by name
- `?search=categoryId:cat-123` - Products in specific category
- `?search=categoryName:*electronics*,status:1` - Active products in electronics category
- `?search=status:0` - Inactive products
- `?search=price:50~150` - Products with net price between 50 and 150
- `?search=salePrice:50~150` - Products with sale price between 50 and 150
- `?search=price>100,orderBy>price` - Products over 100, sorted by net price
- `?search=categoryName:*beauty*,salePrice<50,orderBy>salePrice` - Beauty products under 50, sorted by sale price
- `?search=code:01-PROD123` - Product with specific vendor code
- `?search=orderBy>createdOn` - All products sorted by creation date

**Response:** `200 OK`
```json
{
  "data": [
    {
      "productId": "uuid",
      "companyId": "org-id",
      "name": "Product Name",
      "description": "Product description",
      "unitsPerBox": 12,
      "price": 99.50,
      "imageUrl": "https://...",
      "category": {
        "categoryId": "uuid",
        "name": "Electronics"
      },
      "cabys": {
        "id": "uuid",
        "code": "1234567890123",
        "name": "CABYS Product Name",
        "type": 1
      },
      "unitId": 85,
      "commercialUnitMeasure": "Unidad",
      "isPackaged": false,
      "quantity": 1.0,
      "unitPrice": 99.50,
      "customsPart": null,
      "codes": [
        {
          "codeTypeId": "01",
          "number": "VENDOR-001",
          "description": "Vendor code"
        },
        {
          "codeTypeId": "04",
          "number": "PROD-001",
          "description": null
        }
      ],
      "discounts": [
        {
          "discountTypeId": "01",
          "percentage": 10.0,
          "amount": 9.95,
          "reason": "Volume discount",
          "isAmount": false
        }
      ],
      "taxes": [
        {
          "taxTypeId": "01",
          "amount": 11.94,
          "taxRate": {
            "id": "08",
            "percentage": 13.0
          },
          "taxFactor": null,
          "otherTaxType": null,
          "specialFields": null,
          "isAmount": false
        }
      ],
      "baseAmount": 89.55,
      "salePrice": 101.49
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 12,
    "totalElements": 100,
    "totalPages": 9
  }
}
```

**Note:** Price is populated from order Excel files (Precio Unidad) and updated only if > 0

---

### 2. Get Product by Code
**GET** `/api/organizations/{organization_id}/codes/{hacienda_code}/products/{code}`

Get a specific product by Hacienda code type and code number.

**Path Parameters:**
- `organization_id` (string, required): Organization identifier
- `hacienda_code` (string, required): Hacienda code type (01=Vendor, 02=Buyer, 03=Manufacturer, 04=Internal, 99=Other)
- `code` (string, required): Product code number

**Response:** `200 OK` (same structure as single product in list)

**Errors:**
- `404`: Product not found

**Example:** `/api/organizations/org-123/codes/01/products/VENDOR-001`

---

### 3. Get Product
**GET** `/api/organizations/{organization_id}/products/{product_id}`

Get a specific product by ID.

**Response:** `200 OK` (same structure as single item in list)

**Errors:**
- `404`: Product not found

---

### 4. Create Product
**POST** `/api/organizations/{organization_id}/products`

Create a new product with optional base64 image.

**Request Body:**
```json
{
  "name": "Product Name",
  "description": "Product description",
  "unitsPerBox": 12,
  "price": 99.50,
  "sku": "SKU-001",
  "categoryId": "uuid",
  "image": {
    "data": "base64-encoded-image-data",
    "contentType": "image/png",
    "name": "product.png"
  },
  "cabys": {
    "code": "1234567890123",
    "name": "CABYS Product Name",
    "type": 1
  },
  "unitId": 85,
  "commercialUnitMeasure": "Unidad",
  "isPackaged": false,
  "quantity": 1.0,
  "unitPrice": 99.50,
  "customsPart": null,
  "codes": [
    {
      "codeTypeId": "01",
      "number": "VENDOR-001",
      "description": "Vendor code"
    },
    {
      "codeTypeId": "04",
      "number": "INTERNAL-001",
      "description": "Internal code"
    }
  ],
  "discounts": [
    {
      "discountTypeId": "01",
      "percentage": 10.0,
      "reason": "Volume discount",
      "isAmount": false
    }
  ],
  "taxes": [
    {
      "taxTypeId": "01",
      "taxRate": {
        "id": "08",
        "percentage": 13.0
      },
      "isAmount": false
    }
  ]
}
```

**All fields are optional**

**Image field structure:**
- `data` (required): Base64-encoded image data
- `contentType` (required): MIME type (image/png, image/jpeg, etc.)
- `name` (optional): Filename

**Image Validation:**
- Allowed types: PNG, JPEG, JPG, GIF, WEBP
- Max size: 5MB
- Data URL prefix is automatically stripped

**Fiscal Fields:**
- `cabys`: CABYS catalog entry (code must be exactly 13 digits)
- `codes`: Array of product codes with Hacienda code types
  - **Validation**: No duplicate code type + number combinations allowed across products
  - Example: Cannot have two products with codeTypeId "01" and number "1234"
  - Different code types with same number are allowed (e.g., "01"-"1234" and "02"-"1234")
- `discounts`: Array of discounts (amounts computed by backend)
- `taxes`: Array of taxes (amounts computed by backend)
- `baseAmount`: Manual override for IVACE-07 only (optional)
- `salePrice`: Always computed by backend (never sent in request)

**Response:** `201 Created` (same structure as product response)

**Errors:**
- `400`: Validation error (invalid image format/size, invalid CABYS code, duplicate product codes, etc.)

---

### 5. Update Product
**PUT** `/api/organizations/{organization_id}/products/{product_id}`

Update an existing product. All fields are optional.

**Request Body:** (same as create, all fields optional)

**Response:** `200 OK` (same structure as product response)

**Errors:**
- `400`: Validation error (duplicate product codes, etc.)
- `404`: Product not found

**Note:** When updating codes, the validation excludes the current product to prevent false conflicts.

---

### 6. Update Product Status
**PATCH** `/api/organizations/{organization_id}/products/{product_id}`

Update product active status.

**Request Body:**
```json
{
  "status": 1
}
```
- `status`: 1 = active, 0 = inactive

**Response:** `200 OK` (same structure as product response)

**Errors:**
- `404`: Product not found

---

## Code Types (Hacienda)

Product codes use Hacienda e-invoicing code types:

- `01`: Vendor code (Código del producto del vendedor)
- `02`: Buyer code (Código del producto del comprador)
- `03`: Manufacturer code (Código del producto asignado por el fabricante)
- `04`: Internal code (Código uso interno)
- `99`: Other (Otros)

## Notes
- All endpoints require organization_id in path
- Product uses `isActive` boolean field (not status integer)
- Images are uploaded to S3: `organizations/{org}/products/{id}/image.{ext}`
- If no category is provided, product is assigned to default "uncategorized" category
- Discount and tax amounts are always computed by the backend
- `salePrice` is always computed by the backend (never sent in request)

## Code Storage

Product codes are stored exclusively in the JSONB `codes` array with Hacienda code types:
- Each code has `codeTypeId`, `number`, and optional `description`
- Supports all Hacienda code types (01=Vendor, 02=Buyer, 03=Manufacturer, 04=Internal, 99=Other)
- Used for e-invoicing, fiscal operations, and cross-docking
- Multiple codes of the same type are allowed (e.g., multiple vendor codes)
