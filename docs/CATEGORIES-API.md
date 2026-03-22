# Categories API Documentation

## Overview

The Categories API allows you to manage product categories for your organization. Categories support two images, custom colors, and sorting.

**Base URL:** `/api/organizations/{organization_id}/categories`

---

## Endpoints

### 1. List Categories

Get a paginated list of all categories for an organization.

**Endpoint:** `GET /api/organizations/{organization_id}/categories`

**Query Parameters:**
- `page` (integer, optional): Page number (1-indexed). Default: 1
- `pageSize` (integer, optional): Items per page (1-100). Default: 12

**Response:** `200 OK`

```json
{
  "data": [
    {
      "categoryId": "uuid",
      "organizationId": "org-123",
      "name": "Electronics",
      "slug": "electronics",
      "description": "Electronic products and accessories",
      "backgroundColor": "#F0F0F0",
      "buttonColor": "#007BFF",
      "image1Url": "https://cdn.example.com/organizations/org-123/categories/uuid/image1.png",
      "image2Url": "https://cdn.example.com/organizations/org-123/categories/uuid/image2.jpg",
      "isActive": true,
      "sortOrder": 1
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 12,
    "totalElements": 25,
    "totalPages": 3
  }
}
```

---

### 2. Get Category by ID

Retrieve a specific category by its ID.

**Endpoint:** `GET /api/organizations/{organization_id}/categories/{category_id}`

**Response:** `200 OK`

```json
{
  "categoryId": "uuid",
  "organizationId": "org-123",
  "name": "Electronics",
  "slug": "electronics",
  "description": "Electronic products and accessories",
  "backgroundColor": "#F0F0F0",
  "buttonColor": "#007BFF",
  "image1Url": "https://cdn.example.com/organizations/org-123/categories/uuid/image1.png",
  "image2Url": "https://cdn.example.com/organizations/org-123/categories/uuid/image2.jpg",
  "isActive": true,
  "sortOrder": 1
}
```

**Error Responses:**
- `404 Not Found`: Category not found

---

### 3. Create Category

Create a new category with optional image uploads.

**Endpoint:** `POST /api/organizations/{organization_id}/categories`

**Request Body:**

```json
{
  "name": "Electronics",
  "slug": "electronics",
  "description": "Electronic products and accessories",
  "backgroundColor": "#F0F0F0",
  "buttonColor": "#007BFF",
  "image1": {
    "data": "base64-encoded-image-data",
    "name": "category-banner.png",
    "contentType": "image/png"
  },
  "image2": {
    "data": "base64-encoded-image-data",
    "name": "category-icon.jpg",
    "contentType": "image/jpeg"
  },
  "sortOrder": 1
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Category name |
| `slug` | string | No | URL-friendly identifier (must be unique) |
| `description` | string | No | Category description |
| `backgroundColor` | string | No | Hex color code (default: #FFFFFF) |
| `buttonColor` | string | No | Hex color code (default: #000000) |
| `image1` | ImageDTO | No | First category image |
| `image2` | ImageDTO | No | Second category image |
| `sortOrder` | integer | No | Display order (default: 0) |

**ImageDTO Structure:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | string | Yes | Base64-encoded image data (with or without data URL prefix) |
| `name` | string | No | Filename (e.g., "banner.png"). If not provided, defaults to "image1.{ext}" or "image2.{ext}" |
| `contentType` | string | Yes | MIME type: `image/png`, `image/jpeg`, `image/jpg`, `image/gif`, or `image/webp` |

**Image Requirements:**
- Supported formats: PNG, JPEG, GIF, WEBP
- Maximum size: 5MB per image
- Images are stored in S3 with path: `organizations/{org_id}/categories/{category_id}/{filename}`

**Response:** `201 Created`

```json
{
  "categoryId": "uuid",
  "organizationId": "org-123",
  "name": "Electronics",
  "slug": "electronics",
  "description": "Electronic products and accessories",
  "backgroundColor": "#F0F0F0",
  "buttonColor": "#007BFF",
  "image1Url": "https://cdn.example.com/organizations/org-123/categories/uuid/category-banner.png",
  "image2Url": "https://cdn.example.com/organizations/org-123/categories/uuid/category-icon.jpg",
  "isActive": true,
  "sortOrder": 1
}
```

**Error Responses:**
- `400 Bad Request`: Invalid data (e.g., duplicate slug, invalid image format, image too large)
- `500 Internal Server Error`: Server error

---

### 4. Update Category

Update an existing category. Only provided fields are updated.

**Endpoint:** `PUT /api/organizations/{organization_id}/categories/{category_id}`

**Request Body:**

```json
{
  "name": "Consumer Electronics",
  "description": "Updated description",
  "image1": {
    "data": "base64-encoded-image-data",
    "name": "new-banner.png",
    "contentType": "image/png"
  }
}
```

**Notes:**
- All fields are optional
- Only provided fields will be updated
- To update images, include the `image1` or `image2` object with new image data
- Images are uploaded to S3 and the URL is returned in the response

**Response:** `200 OK`

```json
{
  "categoryId": "uuid",
  "organizationId": "org-123",
  "name": "Consumer Electronics",
  "slug": "electronics",
  "description": "Updated description",
  "backgroundColor": "#F0F0F0",
  "buttonColor": "#007BFF",
  "image1Url": "https://cdn.example.com/organizations/org-123/categories/uuid/new-banner.png",
  "image2Url": "https://cdn.example.com/organizations/org-123/categories/uuid/image2.jpg",
  "isActive": true,
  "sortOrder": 1
}
```

**Error Responses:**
- `400 Bad Request`: Invalid data (e.g., duplicate slug, invalid image)
- `404 Not Found`: Category not found
- `500 Internal Server Error`: Server error

---

### 5. Update Category Status

Update only the active status of a category.

**Endpoint:** `PATCH /api/organizations/{organization_id}/categories/{category_id}`

**Request Body:**

```json
{
  "status": 1
}
```

**Status Values:**
- `1`: Active
- `0`: Inactive

**Response:** `200 OK`

```json
{
  "categoryId": "uuid",
  "organizationId": "org-123",
  "name": "Electronics",
  "slug": "electronics",
  "description": "Electronic products and accessories",
  "backgroundColor": "#F0F0F0",
  "buttonColor": "#007BFF",
  "image1Url": "https://cdn.example.com/organizations/org-123/categories/uuid/image1.png",
  "image2Url": "https://cdn.example.com/organizations/org-123/categories/uuid/image2.jpg",
  "isActive": false,
  "sortOrder": 1
}
```

**Error Responses:**
- `404 Not Found`: Category not found
- `500 Internal Server Error`: Server error

---

### 6. Delete Category

Delete a category permanently.

**Endpoint:** `DELETE /api/organizations/{organization_id}/categories/{category_id}`

**Response:** `204 No Content`

**Error Responses:**
- `404 Not Found`: Category not found
- `500 Internal Server Error`: Server error

---

## Frontend Implementation Guide

### Image Upload Flow

1. **Prepare Image Data**
   - Read the image file as base64
   - Get the file's MIME type
   - Extract the filename

2. **Create Request Payload**

```typescript
interface ImageDTO {
  data: string;           // Base64-encoded image data
  name?: string;          // Optional filename
  contentType: string;    // MIME type
}

interface CategoryRequest {
  name?: string;
  slug?: string;
  description?: string;
  backgroundColor?: string;
  buttonColor?: string;
  image1?: ImageDTO;
  image2?: ImageDTO;
  sortOrder?: number;
}
```

3. **Example: Create Category with Images**

```typescript
async function createCategoryWithImages(
  organizationId: string,
  categoryData: CategoryRequest
): Promise<CategoryResponse> {
  const response = await fetch(
    `/api/organizations/${organizationId}/categories`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(categoryData),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create category');
  }

  return response.json();
}
```

4. **Example: Convert File to Base64**

```typescript
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // Remove data URL prefix if present
      const base64 = result.includes(',') 
        ? result.split(',')[1] 
        : result;
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function uploadCategoryImage(
  organizationId: string,
  categoryId: string,
  imageFile: File,
  imageSlot: 'image1' | 'image2'
) {
  const base64Data = await fileToBase64(imageFile);
  
  const payload = {
    [imageSlot]: {
      data: base64Data,
      name: imageFile.name,
      contentType: imageFile.type,
    },
  };

  return fetch(
    `/api/organizations/${organizationId}/categories/${categoryId}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }
  );
}
```

5. **Image Validation (Client-Side)**

```typescript
function validateImage(file: File): { valid: boolean; error?: string } {
  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
  const maxSize = 5 * 1024 * 1024; // 5MB

  if (!allowedTypes.includes(file.type)) {
    return {
      valid: false,
      error: 'Invalid image type. Allowed: PNG, JPEG, GIF, WEBP',
    };
  }

  if (file.size > maxSize) {
    return {
      valid: false,
      error: 'Image size exceeds 5MB limit',
    };
  }

  return { valid: true };
}
```

### S3 URL Structure

Images are stored in S3 with the following path pattern:

```
organizations/{organization_id}/categories/{category_id}/{filename}
```

**Examples:**
- `organizations/org-123/categories/cat-456/banner.png`
- `organizations/org-123/categories/cat-456/icon.jpg`

The API returns the full CDN URL in the response:
- `image1Url`: Full URL to the first image
- `image2Url`: Full URL to the second image

---

## Error Handling

### Common Error Responses

**400 Bad Request**
```json
{
  "detail": "Invalid image type 'image/bmp'. Allowed: image/png, image/jpeg, image/jpg, image/gif, image/webp"
}
```

**404 Not Found**
```json
{
  "detail": "Category not found"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error message"
}
```

### Image Upload Errors

- **Invalid base64 data**: `"Invalid base64 image data"`
- **Image too large**: `"Image size (6291456 bytes) exceeds maximum allowed (5MB)"`
- **Invalid format**: `"Invalid image type 'image/bmp'. Allowed: image/png, image/jpeg, image/jpg, image/gif, image/webp"`
- **Empty data**: `"Image data is empty"`

---

## Best Practices

1. **Image Optimization**
   - Compress images before upload to reduce file size
   - Use appropriate formats (PNG for graphics, JPEG for photos)
   - Consider using WebP for better compression

2. **Error Handling**
   - Always validate images client-side before upload
   - Handle network errors gracefully
   - Show user-friendly error messages

3. **Performance**
   - Upload images separately from other category data if needed
   - Use loading indicators during upload
   - Consider lazy loading for category images in lists

4. **Slug Management**
   - Generate slugs automatically from category names
   - Validate slug uniqueness before submission
   - Use URL-safe characters only

5. **Image Display**
   - Use the returned CDN URLs directly
   - Implement fallback images for missing images
   - Cache images appropriately
