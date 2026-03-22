# Client Status System

## Status Codes

| Code | Name | Description |
|------|------|-------------|
| 0 | Pending | Auto-created via order, incomplete data |
| 1 | Active | Fully active client |
| 2 | Inactive | Manually deactivated |
| 3 | Deleted | Soft deleted, excluded from queries |

## Unique Constraint

**Key**: `(company_id, client_gln, nationality)`

Same GLN can exist for different nationalities within an organization.

## Automatic Status Transitions

### 1. Order Detail Upload → Status 0 (Pending)
```
Excel Upload → Client auto-created → status = 0
```

### 2. Manual Creation → Status 1 (Active)
```
POST /clients → New client created → status = 1
```

### 3. First Update of Pending → Status 1 (Active)
```
PUT /clients/{id} (status=0) → Auto-promoted → status = 1
```

## API Behavior

### GET /clients
- Returns clients with status 0, 1, or 2
- Excludes deleted (status=3)

### GET /clients/{id}
- Returns client if status is 0, 1, or 2
- Returns 404 if deleted (status=3)

### POST /clients
**Creates new OR reactivates deleted**

```json
{
  ...
}
```

**Logic**:
1. Check if deleted client exists with same (company_id, client_gln, nationality)
2. If exists → Reactivate (status=1) and update all fields
3. If not → Create new client (status=1)

### PUT /clients/{id}
**Updates existing client**

- ✅ Works for status 0, 1, 2
- ❌ Fails for status 3 → "Cannot update deleted client. Use POST to reactivate."
- Auto-promotes status 0 → 1 on first update

### PATCH /clients/{id}
**Updates status only**

```json
{
  "status": 2
}
```

- ✅ Works for status 0, 1, 2
- ❌ Fails for status 3 → "Cannot update deleted client. Use POST to reactivate."

## Workflows

### Delete Client
```
PATCH /clients/{id} {"status": 3}
→ Client soft deleted
→ Excluded from all queries
→ Cannot be updated via PUT/PATCH
```

### Reactivate Deleted Client
```
POST /clients {clientGln, nationality, ...}
→ Finds deleted client with matching unique key
→ Reactivates with status=1
→ Updates all fields
→ Reuses same client_id
```

### Deactivate Client
```
PATCH /clients/{id} {"status": 2}
→ Client inactive
→ Still appears in queries
→ Can be updated via PUT/PATCH
```

### Reactivate Inactive Client
```
PATCH /clients/{id} {"status": 1}
→ Client active again
```

## Error Messages

| Scenario | HTTP | Message |
|----------|------|---------|
| Update deleted client (PUT) | 400 | Cannot update deleted client. Use POST to reactivate. |
| Update deleted client status (PATCH) | 400 | Cannot update deleted client. Use POST to reactivate. |
| Get deleted client | 404 | Client not found |

## Database Queries

All repository methods filter by status:

```python
# Excludes deleted (status=3)
Client.status.in_([0, 1, 2])
```

Exception: `find_by_unique_key()` includes all statuses for reactivation logic.

## Search Filters

Available search parameters:

| Filter | Field | Example |
|--------|-------|----------|
| clientName | Client name | `clientName:*Corp*` |
| clientGln | GLN code | `clientGln:1234567890123` |
| status | Status code | `status:0` |
| nationality | Nationality | `nationality:CR` |
| idNumber | ID number | `idNumber:123456789` |

### Frontend: Finding Pending Clients

When adding or completing a pending client (status=0), search by GLN, nationality, and ID number to validate no repeated clients exist:

```
# Search by nationality and ID
GET /api/organizations/{org_id}/clients?search=nationality:CR,idNumber:123456789

# Or search by GLN
GET /api/organizations/{org_id}/clients?search=clientGln:1234567890123

# Or combine all
GET /api/organizations/{org_id}/clients?search=clientGln:1234567890123,nationality:CR,idNumber:123456789
```

**If a client is found:**
- Launch alert: "Client already exists"
- Disable all form fields
- Enable only the Delete button (to clear the form, not to mark client as deleted)

### Common Search Patterns

```
# Find all pending clients
search=status:0

# Find pending clients by nationality
search=status:0,nationality:CR

# Find client by nationality and ID
search=nationality:CR,idNumber:123456789

# Find active clients sorted by name
search=status:1,orderBy>clientName
```
