# Departments API

## Base URL
`/api/organizations/{organization_id}/clients/{client_id}/departments`

## Endpoints

### 1. List Departments
**GET** `/api/organizations/{organization_id}/clients/{client_id}/departments`

Get paginated list of departments for a client with optional search filters.

**Query Parameters:**
- `page` (integer, optional): Page number (1-indexed). Default: 1
- `pageSize` (integer, optional): Items per page (1-100). Default: 12
- `search` (string, optional): Search filter string

**Search Filters:**
- `departmentCode`: Department code
- `name`: Department name (supports wildcards)
- `supplierCode`: Supplier code

**Sorting:**
- `orderBy>field` (Ascending)
- `orderBy<field` (Descending)
- Sortable fields: `departmentCode`, `name`, `supplierCode`, `createdOn`, `updatedOn`

**Example:** `?search=name:*warehouse*,orderBy>name`

**Response:** `200 OK`
```json
{
  "data": [
    {
      "departmentId": "uuid",
      "companyId": "org-id",
      "clientId": "uuid",
      "departmentCode": "DEPT-001",
      "name": "Warehouse A",
      "supplierCode": "SUP-001"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 12,
    "totalElements": 30,
    "totalPages": 3
  }
}
```

---

### 2. Get Department
**GET** `/api/organizations/{organization_id}/clients/{client_id}/departments/{department_id}`

Get a specific department by ID.

**Response:** `200 OK` (same structure as single item in list)

**Errors:**
- `400`: Invalid department ID format
- `404`: Department not found

---

### 3. Create Department
**POST** `/api/organizations/{organization_id}/clients/{client_id}/departments`

Create a new department.

**Request Body:**
```json
{
  "departmentCode": "DEPT-001",
  "name": "Warehouse A",
  "supplierCode": "SUP-001"
}
```

**Validation:**
- `departmentCode` is required
- `name` and `supplierCode` are optional

**Response:** `201 Created`

**Errors:**
- `422`: Validation error

---

### 4. Update Department
**PUT** `/api/organizations/{organization_id}/clients/{client_id}/departments/{department_id}`

Update an existing department. All fields are optional.

**Request Body:** (same as create, all fields optional)

**Response:** `200 OK`

**Errors:**
- `400`: Invalid department ID format
- `404`: Department not found

---

### 5. Update Department Status
**PATCH** `/api/organizations/{organization_id}/clients/{client_id}/departments/{department_id}`

Update department status.

**Request Body:**
```json
{
  "status": 1
}
```
- `status`: 1 = active, 0 = inactive

**Response:** `200 OK`

**Errors:**
- `400`: Invalid department ID format
- `404`: Department not found

---

### 6. Delete Department
**DELETE** `/api/organizations/{organization_id}/clients/{client_id}/departments/{department_id}`

Soft delete a department.

**Response:** `204 No Content`

**Errors:**
- `400`: Invalid department ID format
- `404`: Department not found

---

## Notes
- All endpoints require organization_id and client_id in path
- Department IDs are UUIDs
- Departments are scoped to a specific client
- Delete is a soft delete (sets status=0, deleted_on=now)
- Unique constraint: (client_id, department_code)
