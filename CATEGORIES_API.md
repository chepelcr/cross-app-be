# Categories API

## Base URL
`/api/organizations/{organization_id}/categories`

## Endpoints

### 1. List Categories
**GET** `/api/organizations/{organization_id}/categories`

Get paginated list of categories for an organization.

**Query Parameters:**
- `page` (integer, optional): Page number (1-indexed). Default: 1
- `pageSize` (integer, optional): Items per page (1-100). Default: 12

**Response:** `200 OK`
```json
{
  "data": [
    {
      "categoryId": "uuid",
      "organizationId": "org-id",
      "name": "Electronics",
      "slug": "electronics",
      "description": "Electronic products",
      "backgroundColor": "#FFFFFF",
      "buttonColor": "#000000",
      "image1Url": "https://...",
      "image2Url": "https://...",
      "isActive": true,
      "sortOrder": 0
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 12,
    "totalElements": 50,
    "totalPages": 5
  }
}
```

---

### 2. Get Category
**GET** `/api/organizations/{organization_id}/categories/{category_id}`

Get a specific category by ID.

**Response:** `200 OK` (same structure as single item in list)

**Errors:**
- `404`: Category not found

---

### 3. Create Category
**POST** `/api/organizations/{organization_id}/categories`

Create a new category.

**Request Body:**
```json
{
  "name": "Electronics",
  "slug": "electronics",
  "description": "Electronic products",
  "backgroundColor": "#FFFFFF",
  "buttonColor": "#000000",
  "image1Url": "https://...",
  "image2Url": "https://...",
  "sortOrder": 0
}
```

**All fields are optional**

**Response:** `201 Created` (same structure as get)

**Errors:**
- `400`: Validation error (e.g., slug already exists)

---

### 4. Update Category
**PUT** `/api/organizations/{organization_id}/categories/{category_id}`

Update an existing category. All fields are optional.

**Request Body:** (same as create, all fields optional)

**Response:** `200 OK`

**Errors:**
- `400`: Validation error (e.g., slug already exists)
- `404`: Category not found

---

### 5. Update Category Status
**PATCH** `/api/organizations/{organization_id}/categories/{category_id}`

Update category active status.

**Request Body:**
```json
{
  "status": 1
}
```
- `status`: 1 = active, 0 = inactive

**Response:** `200 OK`

**Errors:**
- `404`: Category not found

---

### 6. Delete Category
**DELETE** `/api/organizations/{organization_id}/categories/{category_id}`

Delete a category.

**Response:** `204 No Content`

**Errors:**
- `404`: Category not found

---

## Notes
- All endpoints require organization_id in path
- Slug must be unique per organization
- Categories are sorted by sortOrder field
