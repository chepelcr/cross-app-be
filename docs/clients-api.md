# Clients API — Full Reference

> **Base URL:** `/api/organizations/{organization_id}`
> All endpoints require `organization_id` as a path parameter (string).

---

## Table of Contents

1. [Shared Models](#shared-models)
2. [Clients](#clients)
   - [List Clients](#1-list-clients)
   - [Get Client](#2-get-client)
   - [Create Client](#3-create-client)
   - [Update Client](#4-update-client)
   - [Update Client Status](#5-update-client-status)
3. [Stores](#stores)
   - [List Stores](#1-list-stores)
   - [Get Store](#2-get-store)
   - [Create Store](#3-create-store)
   - [Update Store](#4-update-store)
   - [Update Store Status](#5-update-store-status)
   - [Upload Stores (Excel)](#6-upload-stores-excel)
4. [Departments](#departments)
   - [List Departments](#1-list-departments)
   - [Get Department](#2-get-department)
   - [Create Department](#3-create-department)
   - [Update Department](#4-update-department)
   - [Update Department Status](#5-update-department-status)
   - [Delete Department](#6-delete-department)
5. [Search Filter Syntax](#search-filter-syntax)
6. [Status Codes Reference](#status-codes-reference)

---

## Shared Models

### PaginationResponse
Returned in all paginated list responses under the `pagination` key.

| Field | Type | Description |
|---|---|---|
| `page` | `integer` | Current page (0-indexed in response) |
| `pageSize` | `integer` | Items per page |
| `totalElements` | `integer` | Total items across all pages |
| `totalPages` | `integer` | Total number of pages |

```json
{
  "page": 0,
  "pageSize": 12,
  "totalElements": 45,
  "totalPages": 4
}
```

> **Note:** Query params use 1-indexed pages (`page=1`), but the response `pagination.page` is 0-indexed.

---

### StatusRequestDTO
Used by PATCH endpoints on clients, stores, and departments.

| Field | Type | Required | Description |
|---|---|---|---|
| `status` | `integer` | ✅ | New status value (see each resource's status table) |

```json
{ "status": 2 }
```

---

## Clients

### Status Values

| Value | Label | Notes |
|---|---|---|
| `0` | Pending | Initial state (auto-promoted to Active on first update) |
| `1` | Active | Normal active state |
| `2` | Inactive | Soft disabled |
| `3` | Deleted | Soft deleted — cannot be updated; use POST to reactivate |

---

### ClientResponse

| Field | Type | Nullable | Description |
|---|---|---|---|
| `clientId` | `string (UUID)` | ❌ | Unique client identifier |
| `companyId` | `string` | ❌ | Organization/company identifier |
| `clientName` | `string` | ✅ | Display name of the client |
| `clientGln` | `string` | ✅ | Global Location Number |
| `status` | `integer` | ❌ | Client status (0–3, see table above) |
| `businessName` | `string` | ✅ | Legal business name (max 255) |
| `nationality` | `string` | ✅ | ISO 3166-1 numeric country code (e.g. `188` for Costa Rica, `840` for USA) |
| `email` | `string` | ✅ | Contact email (max 255) |
| `identification` | `IdentificationResponse` | ✅ | ID document info (omitted if empty) |
| `phone` | `PhoneResponse` | ✅ | Phone info (omitted if empty) |
| `residence` | `ResidenceResponse` | ✅ | Address info (omitted if empty) |

#### IdentificationResponse

| Field | Type | Nullable | Description |
|---|---|---|---|
| `code` | `string` | ✅ | ID issuer code (max 10) |
| `number` | `string` | ✅ | ID number (9–50 chars) |

#### PhoneResponse

| Field | Type | Nullable | Description |
|---|---|---|---|
| `countryCode` | `string` | ✅ | ISO 3166-1 numeric country code (max 10, e.g. `188`) |
| `areaCode` | `string` | ✅ | Area code (max 10) |
| `number` | `string` | ✅ | Phone number (max 20) |
| `description` | `string` | ✅ | Label/description (max 50) |

#### ResidenceResponse

| Field | Type | Nullable | Description |
|---|---|---|---|
| `stateId` | `integer` | ✅ | State/Province ID |
| `countyId` | `integer` | ✅ | County/Municipality ID |
| `districtId` | `integer` | ✅ | District ID |
| `address` | `string` | ✅ | Free-text address (max 500) |

**Full ClientResponse example:**
```json
{
  "clientId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "companyId": "org-123",
  "clientName": "Acme Corp",
  "clientGln": "7891234500123",
  "status": 1,
  "businessName": "Acme Corporation S.A.",
  "nationality": "CR",
  "email": "contact@acme.com",
  "identification": {
    "code": "CE",
    "number": "123456789"
  },
  "phone": {
    "countryCode": "188",
    "areaCode": "2",
    "number": "22223333",
    "description": "Main office"
  },
  "residence": {
    "stateId": 1,
    "countyId": 5,
    "districtId": 12,
    "address": "300m north of Central Park"
  }
}
```

---

### 1. List Clients

```
GET /api/organizations/{organization_id}/clients
```

**Query Parameters:**

| Param | Type | Default | Required | Description |
|---|---|---|---|---|
| `search` | `string` | — | ❌ | Filter/sort string (see [Search Filter Syntax](#search-filter-syntax)) |
| `page` | `integer` | `1` | ❌ | Page number (min: 1) |
| `pageSize` | `integer` | `12` | ❌ | Items per page (min: 1, max: 100) |

**Searchable/Sortable fields:**

| Field key | Description | Supports wildcard |
|---|---|---|
| `clientName` | Client name | ✅ |
| `clientGln` | GLN code | ❌ |
| `status` | Status value | ❌ |
| `nationality` | Country code | ❌ |
| `idNumber` | ID number | ❌ |
| `createdOn` | Creation date | ❌ |
| `updatedOn` | Last update date | ❌ |

**Response `200`:**
```json
{
  "data": [
    {
      "clientId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "companyId": "org-123",
      "clientName": "Acme Corp",
      "clientGln": "7891234500123",
      "status": 1,
      "businessName": "Acme Corporation S.A.",
      "nationality": "188",
      "email": "contact@acme.com",
      "identification": null,
      "phone": null,
      "residence": null
    }
  ],
  "pagination": {
    "page": 0,
    "pageSize": 12,
    "totalElements": 45,
    "totalPages": 4
  }
}
```

---

### 2. Get Client

```
GET /api/organizations/{organization_id}/clients/{client_id}
```

**Path Parameters:**

| Param | Type | Description |
|---|---|---|
| `organization_id` | `string` | Organization identifier |
| `client_id` | `string (UUID)` | Client UUID |

**Response `200`:** `ClientResponse` (see full example above)

**Error Responses:**

| Status | Description |
|---|---|
| `400` | Invalid UUID format for `client_id` |
| `404` | Client not found |
| `500` | Server error |

---

### 3. Create Client

```
POST /api/organizations/{organization_id}/clients
```

> **Reactivation:** If a soft-deleted client (status=3) exists with the same `companyId` + `clientGln` + `nationality`, it will be **reactivated** and updated instead of creating a duplicate.

**Request Body (`ClientRequestDTO`):**

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `clientName` | `string` | ⚠️ * | — | Display name |
| `clientGln` | `string` | ⚠️ * | — | Global Location Number |
| `businessName` | `string` | ❌ | max 255 | Legal business name |
| `nationality` | `string` | ❌ | 2–3 chars | ISO 3166-1 numeric country code (e.g. `188`) |
| `email` | `string` | ❌ | max 255 | Contact email |
| `identification` | `IdentificationRequest` | ❌ | — | ID document info |
| `phone` | `PhoneRequest` | ❌ | — | Phone info |
| `residence` | `ResidenceRequest` | ❌ | — | Address info |

> ⚠️ \* At least one of `clientName` or `clientGln` is required.

#### IdentificationRequest

| Field | Type | Constraints | Description |
|---|---|---|---|
| `code` | `string` | max 10 | Issuer code |
| `number` | `string` | min 9, max 50 | ID number |

#### PhoneRequest

| Field | Type | Constraints | Description |
|---|---|---|---|
| `countryCode` | `string` | max 10 | ISO 3166-1 numeric country code (e.g. `188`) |
| `areaCode` | `string` | max 10 | Area code |
| `number` | `string` | max 20 | Phone number |
| `description` | `string` | max 50 | Label |

#### ResidenceRequest

| Field | Type | Constraints | Description |
|---|---|---|---|
| `stateId` | `integer` | >= 0 | State ID |
| `countyId` | `integer` | >= 0 | County ID |
| `districtId` | `integer` | >= 0 | District ID |
| `address` | `string` | max 500 | Free-text address |

**Request Body Example:**
```json
{
  "clientName": "Acme Corp",
  "clientGln": "7891234500123",
  "businessName": "Acme Corporation S.A.",
  "nationality": "188",
  "email": "contact@acme.com",
  "identification": {
    "code": "CE",
    "number": "123456789"
  },
  "phone": {
    "countryCode": "188",
    "areaCode": "2",
    "number": "22223333",
    "description": "Main office"
  },
  "residence": {
    "stateId": 1,
    "countyId": 5,
    "districtId": 12,
    "address": "300m north of Central Park"
  }
}
```

**Response `201`:** `ClientResponse`

**Error Responses:**

| Status | Description |
|---|---|
| `400` | Validation error (e.g., missing clientName and clientGln) |
| `500` | Server error |

---

### 4. Update Client

```
PUT /api/organizations/{organization_id}/clients/{client_id}
```

> Cannot update clients with status=3 (Deleted). Use POST to reactivate.
> Pending clients (status=0) are auto-promoted to Active (status=1) on update.

**Path Parameters:** same as Get Client

**Request Body:** same as `ClientRequestDTO` (Create Client)

**Response `200`:** `ClientResponse`

**Error Responses:**

| Status | Description |
|---|---|
| `400` | Invalid UUID or validation error |
| `404` | Client not found |
| `500` | Server error |

---

### 5. Update Client Status

```
PATCH /api/organizations/{organization_id}/clients/{client_id}
```

> Cannot update clients with status=3 (Deleted). Use POST to reactivate.

**Path Parameters:** same as Get Client

**Request Body:**
```json
{ "status": 2 }
```

| Status value | Meaning |
|---|---|
| `1` | Active |
| `2` | Inactive |
| `3` | Deleted (soft delete) |

**Response `200`:** `ClientResponse`

**Error Responses:**

| Status | Description |
|---|---|
| `400` | Invalid UUID format |
| `404` | Client not found |
| `500` | Server error |

---

## Stores

All store endpoints are nested under a client:
```
/api/organizations/{organization_id}/clients/{client_id}/stores
```

### Status Values

| Value | Label |
|---|---|
| `1` | Active |
| `2` | Inactive |
| `3` | Deleted |

---

### StoreResponse

| Field | Type | Nullable | Description |
|---|---|---|---|
| `storeId` | `string (UUID)` | ❌ | Unique store identifier |
| `companyId` | `string` | ❌ | Organization identifier |
| `clientId` | `string (UUID)` | ❌ | Parent client UUID |
| `storeCode` | `string` | ❌ | Store code (required, unique per client) |
| `storeName` | `string` | ✅ | Display name |
| `slotId` | `string` | ✅ | Slot identifier |
| `chain` | `string` | ✅ | Chain name |
| `gln` | `string` | ✅ | Global Location Number |

**Example:**
```json
{
  "storeId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "companyId": "org-123",
  "clientId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "storeCode": "ST001",
  "storeName": "Main Store",
  "slotId": "SLOT-01",
  "chain": "SuperChain",
  "gln": null
}
```

---

### 1. List Stores

```
GET /api/organizations/{organization_id}/clients/{client_id}/stores
```

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `search` | `string` | — | Filter/sort string |
| `page` | `integer` | `1` | Page number (min: 1) |
| `pageSize` | `integer` | `12` | Items per page (min: 1, max: 100) |

**Searchable/Sortable fields:**

| Field key | Description | Supports wildcard |
|---|---|---|
| `storeCode` | Store code | ❌ |
| `storeName` | Store name | ✅ |
| `chain` | Chain name | ✅ |
| `slotId` | Slot ID | ❌ |

**Response `200`:**
```json
{
  "data": [
    {
      "storeId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "companyId": "org-123",
      "clientId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "storeCode": "ST001",
      "storeName": "Main Store",
      "slotId": "SLOT-01",
      "chain": "SuperChain",
      "gln": null
    }
  ],
  "pagination": {
    "page": 0,
    "pageSize": 12,
    "totalElements": 5,
    "totalPages": 1
  }
}
```

---

### 2. Get Store

```
GET /api/organizations/{organization_id}/clients/{client_id}/stores/{store_id}
```

**Path Parameters:**

| Param | Type | Description |
|---|---|---|
| `organization_id` | `string` | Organization identifier |
| `client_id` | `string (UUID)` | Parent client UUID |
| `store_id` | `string (UUID)` | Store UUID |

**Response `200`:** `StoreResponse`

**Error Responses:**

| Status | Description |
|---|---|
| `400` | Invalid UUID format |
| `404` | Store not found |
| `500` | Server error |

---

### 3. Create Store

```
POST /api/organizations/{organization_id}/clients/{client_id}/stores
```

**Request Body (`StoreRequestDTO`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `storeCode` | `string` | ✅ | Store code (unique per client) |
| `storeName` | `string` | ❌ | Display name |
| `slotId` | `string` | ❌ | Slot identifier |
| `chain` | `string` | ❌ | Chain name |

```json
{
  "storeCode": "ST001",
  "storeName": "Main Store",
  "slotId": "SLOT-01",
  "chain": "SuperChain"
}
```

**Response `201`:** `StoreResponse`

**Error Responses:**

| Status | Description |
|---|---|
| `400` | Validation error (e.g., missing storeCode) |
| `500` | Server error |

---

### 4. Update Store

```
PUT /api/organizations/{organization_id}/clients/{client_id}/stores/{store_id}
```

**Request Body:** same as `StoreRequestDTO`

**Response `200`:** `StoreResponse`

**Error Responses:**

| Status | Description |
|---|---|
| `400` | Invalid UUID format |
| `404` | Store not found |
| `500` | Server error |

---

### 5. Update Store Status

```
PATCH /api/organizations/{organization_id}/clients/{client_id}/stores/{store_id}
```

**Request Body:**
```json
{ "status": 2 }
```

**Response `200`:** `StoreResponse`

**Error Responses:**

| Status | Description |
|---|---|
| `400` | Invalid UUID format |
| `404` | Store not found |
| `500` | Server error |

---

### 6. Upload Stores (Excel)

```
POST /api/organizations/{organization_id}/clients/{client_id}/stores/upload
```

Upload an Excel file to bulk-create stores.

**Expected Excel columns:** `Codigo`, `Nombre`, `SLOT ID`, `Cadena`

**Request Body (JSON with base64 file):**
```json
{
  "file": "<base64-encoded Excel file content>",
  "filename": "stores.xlsx"
}
```

**Response `200`:**
```json
{
  "message": "Successfully uploaded 25 stores",
  "count": 25
}
```

**Error Responses:**

| Status | Description |
|---|---|
| `422` | Invalid file format or missing required columns |
| `500` | Server error |

---

## Departments

All department endpoints are nested under a client:
```
/api/organizations/{organization_id}/clients/{client_id}/departments
```

---

### DepartmentResponse

| Field | Type | Nullable | Description |
|---|---|---|---|
| `departmentId` | `string (UUID)` | ❌ | Unique department identifier |
| `companyId` | `string` | ❌ | Organization identifier |
| `clientId` | `string (UUID)` | ❌ | Parent client UUID |
| `departmentCode` | `string` | ❌ | Department code (required, unique per client) |
| `name` | `string` | ✅ | Display name |
| `supplierCode` | `string` | ✅ | Supplier/vendor code |

**Example:**
```json
{
  "departmentId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "companyId": "org-123",
  "clientId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "departmentCode": "DEPT-01",
  "name": "Perishables",
  "supplierCode": "SUP-99"
}
```

---

### 1. List Departments

```
GET /api/organizations/{organization_id}/clients/{client_id}/departments
```

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `search` | `string` | — | Filter/sort string |
| `page` | `integer` | `1` | Page number (min: 1) |
| `pageSize` | `integer` | `12` | Items per page (min: 1, max: 100) |

**Searchable/Sortable fields:**

| Field key | Description | Supports wildcard |
|---|---|---|
| `departmentCode` | Department code | ❌ |
| `name` | Department name | ✅ |
| `supplierCode` | Supplier code | ❌ |
| `createdOn` | Creation date | ❌ |
| `updatedOn` | Last update date | ❌ |

**Response `200`:**
```json
{
  "data": [
    {
      "departmentId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "companyId": "org-123",
      "clientId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "departmentCode": "DEPT-01",
      "name": "Perishables",
      "supplierCode": "SUP-99"
    }
  ],
  "pagination": {
    "page": 0,
    "pageSize": 12,
    "totalElements": 3,
    "totalPages": 1
  }
}
```

---

### 2. Get Department

```
GET /api/organizations/{organization_id}/clients/{client_id}/departments/{department_id}
```

**Path Parameters:**

| Param | Type | Description |
|---|---|---|
| `organization_id` | `string` | Organization identifier |
| `client_id` | `string (UUID)` | Parent client UUID |
| `department_id` | `string (UUID)` | Department UUID |

**Response `200`:** `DepartmentResponse`

**Error Responses:**

| Status | Description |
|---|---|
| `400` | Invalid UUID format |
| `404` | Department not found |
| `500` | Server error |

---

### 3. Create Department

```
POST /api/organizations/{organization_id}/clients/{client_id}/departments
```

**Request Body (`CreateDepartmentDTO`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `departmentCode` | `string` | ✅ | Department code (unique per client) |
| `name` | `string` | ❌ | Display name |
| `supplierCode` | `string` | ❌ | Supplier/vendor code |

```json
{
  "departmentCode": "DEPT-01",
  "name": "Perishables",
  "supplierCode": "SUP-99"
}
```

**Response `201`:** `DepartmentResponse`

**Error Responses:**

| Status | Description |
|---|---|
| `422` | Validation error |
| `500` | Server error |

---

### 4. Update Department

```
PUT /api/organizations/{organization_id}/clients/{client_id}/departments/{department_id}
```

**Request Body (`UpdateDepartmentDTO`):** all fields optional

| Field | Type | Required | Description |
|---|---|---|---|
| `departmentCode` | `string` | ❌ | Department code |
| `name` | `string` | ❌ | Display name |
| `supplierCode` | `string` | ❌ | Supplier/vendor code |

```json
{
  "name": "Fresh Produce",
  "supplierCode": "SUP-100"
}
```

**Response `200`:** `DepartmentResponse`

**Error Responses:**

| Status | Description |
|---|---|
| `400` | Invalid UUID format |
| `404` | Department not found |
| `500` | Server error |

---

### 5. Update Department Status

```
PATCH /api/organizations/{organization_id}/clients/{client_id}/departments/{department_id}
```

**Request Body:**
```json
{ "status": 2 }
```

**Response `200`:** `DepartmentResponse`

**Error Responses:**

| Status | Description |
|---|---|
| `400` | Invalid UUID format |
| `404` | Department not found |
| `500` | Server error |

---

### 6. Delete Department

```
DELETE /api/organizations/{organization_id}/clients/{client_id}/departments/{department_id}
```

Soft deletes the department (sets status=3).

**Response `204`:** No content

**Error Responses:**

| Status | Description |
|---|---|
| `400` | Invalid UUID format |
| `404` | Department not found |
| `500` | Server error |

---

## Search Filter Syntax

The `search` query parameter accepts a comma-separated list of filters:

```
field:value,field2:value2,orderBy>field3
```

### Operators

| Operator | Meaning | Example |
|---|---|---|
| `:` | Equal | `status:1` |
| `!` | Not equal | `status!3` |
| `>` | Greater than (or sort ASC when used with `orderBy`) | `orderBy>clientName` |
| `<` | Less than (or sort DESC when used with `orderBy`) | `orderBy<createdOn` |
| `~` | LIKE (partial match) | `clientName~acme` |

### Wildcard in values

Use `*` as a wildcard in values for fields that support it:

```
clientName:*Acme*        → LIKE '%Acme%'
clientName:Acme*         → LIKE 'Acme%'
```

### Sorting

```
orderBy>clientName       → ORDER BY clientName ASC
orderBy<createdOn        → ORDER BY createdOn DESC
```

### Full examples

```
clientName:*Corp*,status:1,orderBy>clientName
storeName:*test*,orderBy>storeCode
name:*warehouse*,orderBy>name
```

---

## Status Codes Reference

| HTTP Status | Meaning |
|---|---|
| `200` | OK — successful GET, PUT, PATCH |
| `201` | Created — successful POST |
| `204` | No Content — successful DELETE |
| `400` | Bad Request — invalid UUID or validation error |
| `404` | Not Found — resource does not exist |
| `422` | Unprocessable Entity — business rule violation |
| `500` | Internal Server Error |
