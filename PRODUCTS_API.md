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
- `internalCode`: Internal product code
- `description`: Product description (supports wildcards)
- `originalCode`: Original product code
- `code`: Product code
- `name`: Product name (supports wildcards)

**Sorting:**
- `orderBy>field` (Ascending)
- `orderBy<field` (Descending)
- Sortable fields: `internalCode`, `description`, `originalCode`, `code`, `name`

**Example:** `?search=name:*shampoo*,orderBy>internalCode`

**Response:** `200 OK`
```json
{
  "data": [
    {
      "productId": "uuid",
      "companyId": "org-id",
      "internalCode": "PROD-001",
      "originalCode": "ORIG-001",
      "clientArticleCode": "CLIENT-001",
      "code": "CODE-001",
      "name": "Product Name",
      "description": "Product description",
      "unitsPerBox": 12,
      "price": 99.50,
      "imageUrl": "https://...",
      "category": {
        "categoryId": "uuid",
        "name": "Electronics"
      }
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

### 2. Get Product
**GET** `/api/organizations/{organization_id}/products/{product_id}`

Get a specific product by ID.

**Response:** `200 OK` (same structure as single item in list)

**Errors:**
- `404`: Product not found

---

### 3. Create Product
**POST** `/api/organizations/{organization_id}/products`

Create a new product with optional base64 image.

**Request Body:**
```json
{
  "internalCode": "PROD-001",
  "originalCode": "ORIG-001",
  "clientArticleCode": "CLIENT-001",
  "code": "CODE-001",
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
  }
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

**Response:** `201 Created`

**Errors:**
- `400`: Validation error (invalid image format/size)

---

### 4. Update Product
**PUT** `/api/organizations/{organization_id}/products/{product_id}`

Update an existing product. All fields are optional.

**Request Body:** (same as create, all fields optional)

**Response:** `200 OK`

**Errors:**
- `400`: Validation error
- `404`: Product not found

---

### 5. Update Product Status
**PATCH** `/api/organizations/{organization_id}/products/{product_id}`

Update product active status.

**Request Body:**
```json
{
  "status": 1
}
```
- `status`: 1 = active, 0 = inactive

**Response:** `200 OK`

**Errors:**
- `404`: Product not found

---

## Notes
- All endpoints require organization_id in path
- Product uses `isActive` boolean field (not status integer)
- Images are uploaded to S3: `organizations/{org}/products/{id}/image.{ext}`
- If no category is provided, product is assigned to default "uncategorized" category
