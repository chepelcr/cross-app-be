# Clients API

## Base URL
`/api/organizations/{organization_id}/clients`

## Endpoints

### 1. List Clients
**GET** `/api/organizations/{organization_id}/clients`

Get paginated list of clients with optional search filters.

**Query Parameters:**
- `page` (integer, optional): Page number (1-indexed). Default: 1
- `pageSize` (integer, optional): Items per page (1-100). Default: 12
- `search` (string, optional): Search filter string

**Search Filters:**
- `clientName`: Client name (supports wildcards)
- `clientGln`: Client GLN code

**Sorting:**
- `orderBy>field` (Ascending)
- `orderBy<field` (Descending)
- Sortable fields: `clientName`, `clientGln`, `createdOn`, `updatedOn`

**Example:** `?search=clientName:*corp*,orderBy>clientName`

**Response:** `200 OK`
```json
{
  "data": [
    {
      "clientId": "uuid",
      "companyId": "org-id",
      "clientName": "Acme Corp",
      "clientGln": "1234567890123",
      "identification": {
        "type": 1,
        "code": "01",
        "number": "3101123456"
      },
      "businessName": "Company Name S.A.",
      "nationality": "CR",
      "phone": {
        "countryCode": "506",
        "areaCode": "506",
        "number": "88888888",
        "description": "PERSONAL"
      },
      "residence": {
        "stateId": 1,
        "countyId": 1,
        "districtId": 1,
        "address": "100 metros norte del parque central"
      }
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

### 2. Get Client
**GET** `/api/organizations/{organization_id}/clients/{client_id}`

Get a specific client by ID.

**Response:** `200 OK` (same structure as single item in list)

**Errors:**
- `400`: Invalid client ID format
- `404`: Client not found

---

### 3. Create Client
**POST** `/api/organizations/{organization_id}/clients`

Create a new client.

**Request Body:**
```json
{
  "clientName": "Acme Corp",
  "clientGln": "1234567890123",
  "identification": {
    "type": 1,
    "code": "01",
    "number": "3101123456"
  },
  "businessName": "Company Name S.A.",
  "nationality": "CR",
  "phone": {
    "countryCode": "506",
    "areaCode": "506",
    "number": "88888888",
    "description": "PERSONAL"
  },
  "residence": {
    "stateId": 1,
    "countyId": 1,
    "districtId": 1,
    "address": "100 metros norte del parque central"
  }
}
```

**All fields are optional**

**Validation:**
- At least one of `clientName` or `clientGln` is required
- `identification.number` must be at least 9 characters if provided
- `nationality` must be 2-3 characters if provided

**Response:** `201 Created`

**Errors:**
- `400`: Validation error

---

### 4. Update Client
**PUT** `/api/organizations/{organization_id}/clients/{client_id}`

Update an existing client. All fields are optional.

**Request Body:** (same as create, all fields optional)

**Response:** `200 OK`

**Errors:**
- `400`: Invalid client ID format
- `404`: Client not found

---

### 5. Update Client Status
**PATCH** `/api/organizations/{organization_id}/clients/{client_id}`

Update client status.

**Request Body:**
```json
{
  "status": 1
}
```
- `status`: 1 = active, 0 = inactive

**Response:** `200 OK`

**Errors:**
- `400`: Invalid client ID format
- `404`: Client not found

---

## Notes
- All endpoints require organization_id in path
- Client IDs are UUIDs
- Status field uses AuditMixin pattern (1=active, 0=inactive)
