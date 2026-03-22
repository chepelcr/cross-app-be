# Orders Search API

The `GET /api/organizations/{organization_id}/orders` endpoint supports a `search` query parameter for filtering, sorting, and pagination.

---

## Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `search` | string | — | Search filter string (see syntax below) |
| `page` | int | 1 | Page number (1-indexed) |
| `pageSize` | int | 12 | Items per page (1-100) |

---

## Search Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `:` | Equal | `orderStatus:pending` |
| `!` | Not equal | `orderStatus!cancelled` |
| `>` | Greater than | `deliveryDate>01/02/2025` |
| `<` | Less than | `deliveryDate<28/02/2025` |
| `~` | Like (contains) | `clientName~corp` |

---

## Between (Range)

For date fields that support between, use `~` inside the value to define a range:

| Syntax | Description | Example |
|--------|-------------|---------|
| `field:min~max` | Between values | `deliveryDate:01/02/2025~28/02/2025` |
| `field!min~max` | Not between values | `deliveryDate!01/02/2025~28/02/2025` |

---

## Search Filters

| Filter | Field | Wildcards | Between | Description |
|--------|-------|-----------|---------|-------------|
| `documentNumber` | document_number | Yes (auto-like) | No | Document number |
| `clientName` | client_name | Yes (auto-like) | No | Client name |
| `supplierName` | supplier_name | Yes (auto-like) | No | Supplier name |
| `deliverToName` | deliver_to_name | Yes (auto-like) | No | Delivery place name |
| `confirmationNumber` | confirmation_number | Yes (auto-like) | No | Confirmation number |
| `deliveryDate` | delivery_date | No | Yes | Delivery date (dd/mm/yyyy) |
| `creationDate` | creation_date | No | Yes | Creation date (dd/mm/yyyy) |
| `orderStatus` | order_status | No | No | Order status |
| `deliverToCode` | deliver_to_code | No | No | Delivery place code |

### Auto-like fields

Fields marked **auto-like** (`documentNumber`, `clientName`, `supplierName`, `deliverToName`, `confirmationNumber`) automatically apply case-insensitive contains matching. This means:

- `clientName:corp` behaves the same as `clientName:*corp*`
- No need to add `*` wildcards for these fields

### Order Status Values

| Value | Description |
|-------|-------------|
| `pending` | Initial state |
| `processing` | Being processed |
| `shipped` | Shipped |
| `delivered` | Delivered |
| `cancelled` | Cancelled |

---

## Wildcards

For auto-like fields, wildcards are optional but can be used for more control:

| Pattern | Description | Example | Matches |
|---------|-------------|---------|---------|
| `*value*` | Contains | `clientName:*ana*` | Ariana, Melania |
| `value*` | Starts with | `clientName:Al*` | Alberto, Alana |
| `*value` | Ends with | `clientName:*el` | Daniel, Miguel |

---

## AND / OR Logic

- Conditions separated by `,` (commas) outside parentheses → **AND**
- Conditions grouped inside `()` (parentheses) → **OR**

| Syntax | Logic |
|--------|-------|
| `a,b` | a AND b |
| `(a,b)` | a OR b |
| `a,(b,c)` | a AND (b OR c) |

---

## Sorting

| Syntax | Direction |
|--------|-----------|
| `orderBy>field` | Ascending (ASC) |
| `orderBy<field` | Descending (DESC) |

### Sortable Fields

`documentNumber`, `clientName`, `supplierName`, `deliveryDate`, `creationDate`, `orderStatus`, `createdOn`, `updatedOn`

Default sort: `createdOn` descending.

---

## Examples

### Simple filters

```
search=orderStatus:pending
search=clientName:walmart
search=documentNumber:2446
```

### Combined filters (AND)

```
search=clientName:walmart,orderStatus:pending
search=deliverToCode:CD01,orderStatus:processing
```

### OR grouping

```
search=(orderStatus:pending,orderStatus:processing)
search=(deliverToCode:CD01,deliverToCode:CD02)
```

### Mixed AND + OR

```
search=clientName:walmart,(orderStatus:pending,orderStatus:processing)
search=supplierName:moda,(deliverToCode:CD01,deliverToCode:CD02),orderBy>deliveryDate
```

### Date range (BETWEEN)

```
search=deliveryDate:01/02/2025~28/02/2025
search=creationDate:01/01/2025~31/01/2025,orderStatus:pending
```

### With sorting

```
search=orderStatus:pending,orderBy>deliveryDate
search=clientName:walmart,orderBy<createdOn
search=orderBy>documentNumber
```

### Full example

```
GET /api/organizations/ORG-001/orders?search=clientName:walmart,(orderStatus:pending,orderStatus:processing),deliveryDate:01/02/2025~28/02/2025,orderBy>deliveryDate&page=1&pageSize=20
```

This returns: orders where client name contains "walmart" **AND** (status is pending **OR** processing) **AND** delivery date is between Feb 1-28, sorted by delivery date ascending, page 1 with 20 items.
