# Product Search Guide

## Overview

The product search system provides a flexible and powerful way to filter, search, and sort products using a query string syntax. This guide covers all available filters, operators, and usage patterns.

---

## Base Endpoint

```
GET /api/organizations/{organization_id}/products
```

**Query Parameters:**
- `page` (integer, optional): Page number (1-indexed). Default: 1
- `pageSize` (integer, optional): Items per page (1-100). Default: 12
- `search` (string, optional): Search filter string

---

## Search Syntax

### Basic Format
```
field:value
```

### Multiple Filters
Separate filters with commas:
```
field1:value1,field2:value2,field3:value3
```

**Default behavior:** Filters are combined with AND logic.

### OR Logic with Parentheses
Group filters inside parentheses to apply OR logic:
```
(field1:value1,field2:value2)
```

**Combined AND/OR:**
```
field1:value1,(field2:value2,field3:value3)
```
This means: `field1 = value1 AND (field2 = value2 OR field3 = value3)`

### Example
```
GET /api/organizations/org-123/products?search=name:shampoo,status:1,price:10~50
```
Finds products where name contains "shampoo" AND status is active AND price is between 10-50.

```
GET /api/organizations/org-123/products?search=(name:shampoo,categoryName:Hair),status:1
```
Finds products where (name contains "shampoo" OR category contains "Hair") AND status is active.

---

## Available Filters

### 1. Text Filters (Support Wildcards)

#### `name`
Product name search with automatic partial matching.

**Wildcards Required:** No - Automatically uses LIKE for partial matching

**Examples:**
```
name:shampoo                    # Automatically searches for products containing "shampoo"
name:Organic                    # Automatically searches for products containing "Organic"
name:*Gel                       # Explicit wildcard still works (ends with "Gel")
```

**Note:** Product name has `always_like=True`, which means it automatically performs case-insensitive partial matching without requiring wildcards. This makes search more user-friendly.

#### `description`
Product description search with automatic partial matching.

**Wildcards Required:** No - Automatically uses LIKE for partial matching

**Examples:**
```
description:moisturizing        # Automatically searches for descriptions containing "moisturizing"
description:Professional        # Automatically searches for descriptions containing "Professional"
```

#### `categoryName`
Category name search with automatic partial matching (join field).

**Wildcards Required:** No - Automatically uses LIKE for partial matching

**Examples:**
```
categoryName:Beauty             # Automatically searches for categories containing "Beauty"
categoryName:Hair               # Automatically searches for categories containing "Hair"
```

---

### 2. Exact Match Filters

#### `categoryId`
Filter by category ID (exact match).

**Examples:**
```
categoryId:cat-123              # Products in category cat-123
```

#### `status`
Filter by active status.

**Values:**
- `1` = Active products
- `0` = Inactive products

**Examples:**
```
status:1                        # Active products only
status:0                        # Inactive products only
```

---

### 3. Code Filter (Special)

#### `code`
Search in the JSONB codes array. Supports two formats:

**Format 1: With Code Type**
```
code:01-VENDOR123               # Search for codeTypeId "01" and number "VENDOR123"
code:04-INTERNAL456             # Search for codeTypeId "04" and number "INTERNAL456"
```

**Format 2: Without Code Type**
```
code:PROD123                    # Search all code types for number "PROD123"
```

**Hacienda Code Types:**
- `01` = Vendor code
- `02` = Buyer code
- `03` = Manufacturer code (Barcode)
- `04` = Internal code
- `99` = Other

**Examples:**
```
code:01-VENDOR001               # Specific vendor code
code:03-7501234567890           # Barcode lookup
code:PROD123                    # Any code type with this number
```

---

### 4. Numeric Filters (Support Range Operations)

#### `price`
Filter by net price (integer field).

**Operators:**
- `:` = Exact match
- `>` = Greater than
- `<` = Less than
- `~` = Between (range)

**Examples:**
```
price:100                       # Exactly 100
price>50                        # Greater than 50
price<200                       # Less than 200
price:50~150                    # Between 50 and 150 (inclusive)
```

#### `salePrice`
Filter by calculated sale price (decimal field).

**Operators:**
- `:` = Exact match
- `>` = Greater than
- `<` = Less than
- `~` = Between (range)

**Examples:**
```
salePrice:99.99                 # Exactly 99.99
salePrice>100                   # Greater than 100
salePrice<50                    # Less than 50
salePrice:50~150                # Between 50 and 150 (inclusive)
```

---

### 5. Timestamp Filters

#### `createdOn`
Product creation timestamp.

**Examples:**
```
createdOn:2024-01-01            # Created on specific date
```

#### `updatedOn`
Product last update timestamp.

**Examples:**
```
updatedOn:2024-01-01            # Updated on specific date
```

---

## Sorting

### Syntax
```
orderBy>field                   # Ascending order
orderBy<field                   # Descending order
```

### Sortable Fields
- `description`
- `name`
- `price`
- `salePrice`
- `createdOn`
- `updatedOn`

### Examples
```
orderBy>name                    # Sort by name A-Z
orderBy<price                   # Sort by price high to low
orderBy>salePrice               # Sort by sale price low to high
orderBy<createdOn               # Sort by newest first
```

---

## Complete Examples

### Example 1: Basic Text Search
```
GET /api/organizations/org-123/products?search=name:shampoo
```
Find all products with "shampoo" in the name (automatic partial matching).

---

### Example 2: Category Filter
```
GET /api/organizations/org-123/products?search=categoryName:Beauty,status:1
```
Find all active products in categories containing "Beauty" (automatic partial matching).

---

### Example 3: Price Range
```
GET /api/organizations/org-123/products?search=price:50~150,orderBy>price
```
Find products priced between 50 and 150, sorted by price ascending.

---

### Example 4: Sale Price Filter
```
GET /api/organizations/org-123/products?search=salePrice<100,status:1,orderBy<salePrice
```
Find active products with sale price under 100, sorted by sale price descending.

---

### Example 5: Multiple Filters
```
GET /api/organizations/org-123/products?search=categoryName:Hair,price:20~100,status:1,orderBy>name
```
Find active hair products priced between 20 and 100, sorted by name (automatic partial matching on category name).

---

### Example 6: Code Lookup
```
GET /api/organizations/org-123/products?search=code:01-VENDOR123
```
Find product with vendor code "VENDOR123".

---

### Example 7: Complex Query
```
GET /api/organizations/org-123/products?search=categoryName:Beauty,salePrice:50~200,status:1,orderBy>salePrice&page=1&pageSize=20
```
Find active beauty products with sale price 50-200, sorted by sale price, 20 per page (automatic partial matching on category name).

---

### Example 8: Inactive Products
```
GET /api/organizations/org-123/products?search=status:0,orderBy<updatedOn
```
Find all inactive products, sorted by most recently updated.

---

### Example 9: Category and Price
```
GET /api/organizations/org-123/products?search=categoryId:cat-123,price>100
```
Find products in specific category with price over 100.

---

### Example 10: Text Search with Price Range
```
GET /api/organizations/org-123/products?search=name:Organic,salePrice:30~80,orderBy>name
```
Find products with "Organic" in name, sale price 30-80, sorted by name (automatic partial matching).

---

### Example 11: OR Logic - Search by Name OR Category
```
GET /api/organizations/org-123/products?search=(name:shampoo,categoryName:Hair)
```
Find products where name contains "shampoo" OR category contains "Hair".

---

### Example 12: Combined AND/OR Logic
```
GET /api/organizations/org-123/products?search=(name:shampoo,description:conditioner),status:1,price:10~50
```
Find active products priced 10-50 where (name contains "shampoo" OR description contains "conditioner").

---

### Example 13: Multiple OR Groups
```
GET /api/organizations/org-123/products?search=(categoryName:Hair,categoryName:Beauty),(price<20,price>100)
```
Find products where (category is Hair OR Beauty) AND (price is less than 20 OR greater than 100).

---

### Example 14: OR with Status Filter
```
GET /api/organizations/org-123/products?search=(name:organic,name:natural),status:1,orderBy>price
```
Find active products where name contains "organic" OR "natural", sorted by price.

---

## Operators Reference

| Operator | Symbol | Description | Example |
|----------|--------|-------------|---------|
| Equal | `:` | Exact match (or LIKE for text fields) | `status:1` |
| Not Equal | `!` | Not equal to | `status!0` |
| Greater Than | `>` | Greater than | `price>100` |
| Less Than | `<` | Less than | `price<50` |
| Like | `*` | Wildcard match (optional for text fields) | `name:*shampoo*` |
| Between | `~` | Range (inclusive) | `price:50~150` |
| AND | `,` | Combine filters (outside parentheses) | `name:shampoo,status:1` |
| OR | `( , )` | Group filters with OR logic | `(name:shampoo,categoryName:Hair)` |

---

## Wildcard Patterns

**Important:** Product text fields (name, description, categoryName) have automatic partial matching enabled (`always_like=True`). Wildcards are optional but still supported for advanced patterns.

| Pattern | Description | Example | Behavior |
|---------|-------------|---------|----------|
| `text` | Automatic contains (recommended) | `name:shampoo` | Matches "Hair Shampoo", "Shampoo Bar", "SHAMPOO" |
| `*text*` | Explicit contains (optional) | `name:*shampoo*` | Same as above - wildcards are optional |
| `text*` | Starts with (explicit) | `name:Organic*` | "Organic Soap", "Organic Oil" |
| `*text` | Ends with (explicit) | `name:*Gel` | "Hair Gel", "Styling Gel" |

---

## Response Format

```json
{
  "data": [
    {
      "productId": "uuid",
      "companyId": "org-id",
      "name": "Product Name",
      "description": "Product description",
      "price": 100,
      "salePrice": 89.55,
      "imageUrl": "https://...",
      "isActive": true,
      "category": {
        "categoryId": "uuid",
        "name": "Category Name"
      },
      "codes": [
        {
          "codeTypeId": "01",
          "number": "VENDOR-001",
          "description": "Vendor code"
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 12,
    "totalElements": 45,
    "totalPages": 4
  }
}
```

---

## Frontend Implementation

### TypeScript Example

```typescript
interface ProductSearchParams {
  organizationId: string;
  page?: number;
  pageSize?: number;
  filters?: {
    name?: string;
    description?: string;
    categoryId?: string;
    categoryName?: string;
    status?: 0 | 1;
    priceMin?: number;
    priceMax?: number;
    salePriceMin?: number;
    salePriceMax?: number;
    code?: string;
  };
  sortBy?: string;
  sortDirection?: 'asc' | 'desc';
}

function buildSearchQuery(params: ProductSearchParams): string {
  const filters: string[] = [];
  
```typescript
```typescript
  // Text filters - automatic partial matching (no wildcards needed!)
  // The backend automatically applies LIKE for these fields
  if (params.filters?.name) {
    filters.push(`name:${params.filters.name}`);
  }
  
  if (params.filters?.description) {
    filters.push(`description:${params.filters.description}`);
  }
  
  if (params.filters?.categoryName) {
    filters.push(`categoryName:${params.filters.categoryName}`);
  }
  
  // Exact match filters
  if (params.filters?.categoryId) {
    filters.push(`categoryId:${params.filters.categoryId}`);
  }
  
  if (params.filters?.status !== undefined) {
    filters.push(`status:${params.filters.status}`);
  }
  
  // Price range
  if (params.filters?.priceMin !== undefined && params.filters?.priceMax !== undefined) {
    filters.push(`price:${params.filters.priceMin}~${params.filters.priceMax}`);
  } else if (params.filters?.priceMin !== undefined) {
    filters.push(`price>${params.filters.priceMin}`);
  } else if (params.filters?.priceMax !== undefined) {
    filters.push(`price<${params.filters.priceMax}`);
  }
  
  // Sale price range
  if (params.filters?.salePriceMin !== undefined && params.filters?.salePriceMax !== undefined) {
    filters.push(`salePrice:${params.filters.salePriceMin}~${params.filters.salePriceMax}`);
  } else if (params.filters?.salePriceMin !== undefined) {
    filters.push(`salePrice>${params.filters.salePriceMin}`);
  } else if (params.filters?.salePriceMax !== undefined) {
    filters.push(`salePrice<${params.filters.salePriceMax}`);
  }
  
  // Code filter
  if (params.filters?.code) {
    filters.push(`code:${params.filters.code}`);
  }
  
  // Sorting
  if (params.sortBy) {
    const direction = params.sortDirection === 'desc' ? '<' : '>';
    filters.push(`orderBy${direction}${params.sortBy}`);
  }
  
  return filters.join(',');
}

// Usage example
async function searchProducts(params: ProductSearchParams) {
  const searchQuery = buildSearchQuery(params);
  const url = new URL(`/api/organizations/${params.organizationId}/products`, window.location.origin);
  
  if (searchQuery) {
    url.searchParams.set('search', searchQuery);
  }
  if (params.page) {
    url.searchParams.set('page', params.page.toString());
  }
  if (params.pageSize) {
    url.searchParams.set('pageSize', params.pageSize.toString());
  }
  
  const response = await fetch(url.toString());
  return response.json();
}

```typescript
// Example calls
searchProducts({
  organizationId: 'org-123',
  filters: {
    name: 'shampoo',
    status: 1,
    priceMin: 50,
    priceMax: 150
  },
  sortBy: 'name',
  sortDirection: 'asc',
  page: 1,
  pageSize: 20
});

// For OR logic, build the query manually
const orQuery = '(name:shampoo,categoryName:Hair),status:1';
const url = `/api/organizations/org-123/products?search=${encodeURIComponent(orQuery)}`;
```

### Advanced: Building OR Queries

```typescript
interface OrGroup {
  filters: Array<{ field: string; value: string }>;
}

function buildOrQuery(orGroups: OrGroup[], andFilters: Record<string, string>): string {
  const parts: string[] = [];
  
  // Add OR groups
  orGroups.forEach(group => {
    const groupFilters = group.filters.map(f => `${f.field}:${f.value}`).join(',');
    parts.push(`(${groupFilters})`);
  });
  
  // Add AND filters
  Object.entries(andFilters).forEach(([field, value]) => {
    parts.push(`${field}:${value}`);
  });
  
  return parts.join(',');
}

// Usage
const query = buildOrQuery(
  [
    // OR group 1: name OR category
    {
      filters: [
        { field: 'name', value: 'shampoo' },
        { field: 'categoryName', value: 'Hair' }
      ]
    }
  ],
  // AND filters
  {
    status: '1',
    'price': '10~50'
  }
);
// Result: "(name:shampoo,categoryName:Hair),status:1,price:10~50"
```

---

## Best Practices

### 1. Text Search is Automatic
```
✅ Good: name:shampoo            # Automatic partial match (no wildcards needed!)
✅ Good: name:Organic Shampoo    # Automatic partial match
✅ Also works: name:*shampoo*    # Explicit wildcards still work
```

**Important:** Product text fields (name, description, categoryName) have `always_like=True`, which means they automatically perform case-insensitive partial matching. No wildcards needed!

### 2. Combine Filters for Precision
```
✅ Good: categoryName:Beauty,status:1,price:20~100
✅ Good: (name:shampoo,categoryName:Hair),status:1
❌ Avoid: name:product         # Too broad
```

### 3. Use OR Logic for Flexibility
```
✅ Good: (name:shampoo,name:conditioner),status:1
✅ Good: (categoryName:Hair,categoryName:Beauty)
✅ Good: (name:organic,description:natural),price<50
```

### 4. Use Appropriate Price Filters
```
✅ Good: price:50~150            # Range for browsing
✅ Good: price>100               # Minimum price
✅ Good: salePrice<50            # Maximum sale price
```

### 4. Sort Results
```
✅ Good: name:*shampoo*,orderBy>price     # Sorted results
❌ Avoid: name:*shampoo*                  # Unsorted
```

### 5. Pagination
```
✅ Good: ?search=...&page=1&pageSize=20
❌ Avoid: ?search=...&pageSize=1000      # Too many results
```

---

## Common Use Cases

### 1. Product Catalog Browsing
```
categoryName:Beauty,status:1,orderBy>name
```

### 2. Price Range Shopping
```
salePrice:50~150,status:1,orderBy>salePrice
```

### 3. Search by Name
```
name:shampoo,status:1,orderBy>name
```

### 4. Inventory Management (Inactive Products)
```
status:0,orderBy<updatedOn
```

### 5. Category Management
```
categoryId:cat-123,orderBy>name
```

### 6. Barcode Lookup
```
code:03-7501234567890
```

### 7. Vendor Code Lookup
```
code:01-VENDOR123
```

### 8. Budget Shopping
```
salePrice<50,status:1,orderBy>salePrice
```

### 9. Premium Products
```
price>200,status:1,orderBy<price
```

### 10. Recently Added Products
```
status:1,orderBy<createdOn
```

---

## Logical Operators

### AND Logic (Default)
Filters separated by commas outside parentheses are combined with AND:

```
name:shampoo,status:1,price:10~50
```
**Means:** name contains "shampoo" AND status is active AND price is 10-50

### OR Logic (Parentheses)
Filters inside parentheses are combined with OR:

```
(name:shampoo,categoryName:Hair)
```
**Means:** name contains "shampoo" OR category contains "Hair"

### Combined AND/OR
Mix both for complex queries:

```
(name:shampoo,description:conditioner),status:1,price<50
```
**Means:** (name contains "shampoo" OR description contains "conditioner") AND status is active AND price is less than 50

### Multiple OR Groups
```
(categoryName:Hair,categoryName:Beauty),(price<20,price>100)
```
**Means:** (category is Hair OR Beauty) AND (price < 20 OR price > 100)

### Practical Examples

**Find products by multiple names:**
```
(name:shampoo,name:conditioner,name:soap),status:1
```

**Find products in multiple categories:**
```
(categoryName:Hair,categoryName:Beauty,categoryName:Skin),price:10~50
```

**Find products with specific characteristics:**
```
(name:organic,name:natural,name:eco),status:1,salePrice<30
```

**Complex category and price filtering:**
```
categoryName:Beauty,(price<20,price>100),status:1
```

---

## Error Handling

### Invalid Filter Field
```
Response: 422 Unprocessable Entity
{
  "detail": "Invalid search field: invalidField"
}
```

### Invalid Operator
```
Response: 422 Unprocessable Entity
{
  "detail": "Invalid operator for field: price"
}
```

### Invalid Value Format
```
Response: 422 Unprocessable Entity
{
  "detail": "Invalid value format for field: price"
}
```

---

## Performance Tips

1. **Use specific filters** to reduce result set size
2. **Limit page size** to reasonable values (12-50)
3. **Use categoryId** instead of categoryName when possible (faster)
4. **Avoid wildcards at the start** of text searches when possible (`*text` is slower than `text*`)
5. **Use price ranges** instead of multiple greater/less than filters

---

## Summary

The product search system provides:
- ✅ Automatic partial text search (no wildcards needed for name, description, categoryName)
- ✅ Numeric range filters (price, salePrice)
- ✅ Category filtering (by ID or name)
- ✅ Status filtering (active/inactive)
- ✅ Code lookup (with or without code type)
- ✅ Multiple sort options
- ✅ Pagination support
- ✅ Combinable filters for precise results
- ✅ **OR logic with parentheses** for flexible queries
- ✅ **AND/OR combinations** for complex filtering

**Key Features:**
- Text fields use `always_like=True` for automatic case-insensitive partial matching
- Use parentheses `()` to group filters with OR logic
- Filters outside parentheses are combined with AND logic
- Mix AND/OR for powerful search capabilities
