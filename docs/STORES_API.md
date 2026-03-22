# Stores API

## Base URL
`/api/organizations/{organization_id}/clients/{client_id}/stores`

## Endpoints

### 1. List Stores
**GET** `/api/organizations/{organization_id}/clients/{client_id}/stores`

Get paginated list of stores for a client with optional search filters.

**Query Parameters:**
- `page` (integer, optional): Page number (1-indexed). Default: 1
- `pageSize` (integer, optional): Items per page (1-100). Default: 12
- `search` (string, optional): Search filter string

**Search Filters:**
- `storeCode`: Store code
- `storeName`: Store name (supports wildcards)
- `chain`: Chain name (supports wildcards)
- `slotId`: Slot ID

**Sorting:**
- `orderBy>field` (Ascending)
- `orderBy<field` (Descending)

**Example:** `?search=storeName:*test*,orderBy>storeCode`

**Response:** `200 OK`
```json
{
  "data": [
    {
      "storeId": "uuid",
      "companyId": "org-id",
      "clientId": "uuid",
      "storeCode": "STORE-001",
      "storeName": "Main Store",
      "slotId": "SLOT-A1",
      "chain": "Chain Name"
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

### 2. Get Store
**GET** `/api/organizations/{organization_id}/clients/{client_id}/stores/{store_id}`

Get a specific store by ID.

**Response:** `200 OK` (same structure as single item in list)

**Errors:**
- `400`: Invalid store ID format
- `404`: Store not found

---

### 3. Upload Stores (Excel)
**POST** `/api/organizations/{organization_id}/clients/{client_id}/stores/upload`

Upload stores from an Excel file.

**Request Body:**
```json
{
  "fileName": "stores.xlsx",
  "fileContent": "base64-encoded-excel-file"
}
```

**Excel Format:**
- Required column: `Codigo` (store code)
- Optional columns: `Nombre` (name), `SLOT ID`, `Cadena` (chain)

**Response:** `200 OK`
```json
{
  "message": "Successfully uploaded 25 stores",
  "count": 25
}
```

**Errors:**
- `422`: Validation error (missing required column)

---

### 4. Create Store
**POST** `/api/organizations/{organization_id}/clients/{client_id}/stores`

Create a new store.

**Request Body:**
```json
{
  "storeCode": "STORE-001",
  "storeName": "Main Store",
  "slotId": "SLOT-A1",
  "chain": "Chain Name"
}
```

**Validation:**
- `storeCode` is required (validated at DTO level)
- Other fields are optional

**Response:** `201 Created`

**Errors:**
- `400`: Validation error

---

### 5. Update Store
**PUT** `/api/organizations/{organization_id}/clients/{client_id}/stores/{store_id}`

Update an existing store. All fields are optional.

**Request Body:** (same as create, all fields optional)

**Response:** `200 OK`

**Errors:**
- `400`: Invalid store ID format
- `404`: Store not found

---

### 6. Update Store Status
**PATCH** `/api/organizations/{organization_id}/clients/{client_id}/stores/{store_id}`

Update store status.

**Request Body:**
```json
{
  "status": 1
}
```
- `status`: 1 = active, 0 = inactive

**Response:** `200 OK`

**Errors:**
- `400`: Invalid store ID format
- `404`: Store not found

---

## Notes
- All endpoints require organization_id and client_id in path
- Store IDs are UUIDs
- Stores are scoped to a specific client
- Excel upload performs upsert (creates or updates based on store_code)
- Unique constraint: (organization_id, client_id, store_code)
