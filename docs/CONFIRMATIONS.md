# Confirmations API

Orders delivered to the same place are grouped under a **confirmation**. Each confirmation has a user-provided confirmation number that replaces the BGM011 field in crossdocking reports and PDFs.

Orders from **different days** can be added to the same confirmation as long as:
- No order has a delivery date **in the past**
- All orders are within the **same month and year** (e.g., mixing February and March is not allowed)

The confirmation's `delivery_date` is automatically set to the **earliest** delivery date among all linked orders. All orders in the confirmation are updated to use this earliest date.

---

## Status Codes

Both orders and confirmations share the same status codes:

| Code | Status | Description |
|------|--------|-------------|
| 1 | `pending` | Initial state |
| 2 | `processing` | Default when a confirmation is created |
| 3 | `shipped` | Marked as sent — **triggers delivery email** |
| 4 | `delivered` | Delivery confirmed |
| 5 | `cancelled` | Cancelled |

---

## Endpoints

Base path: `/api/organizations/{organization_id}/confirmations`

### Create Confirmation

**POST** `/api/organizations/{organization_id}/confirmations`

Creates a confirmation and optionally links orders to it. Linked orders get their delivery date updated across DB, Excel files in S3, and regenerated PDFs.

**Request body:**
```json
{
  "confirmation_number": "CONF-001",
  "document_numbers": ["2446", "2447"]
}
```

- `confirmation_number` (required) — User-provided identifier, must be unique per organization
- `document_numbers` (required, min 1) — List of order document numbers to link

The confirmation's `delivery_date`, `deliver_to_code`, and `deliver_to_name` are **automatically set** from the linked orders.

**Response:** `ConfirmationResponse` (see below)

**Errors:**
- `409` — Confirmation number already exists
- `404` — One or more orders not found
- `422` — Order delivery date is in the past, or orders span different months

---

### Update Confirmation

**PUT** `/api/organizations/{organization_id}/confirmations/{confirmation_number}`

Adds more orders to an existing confirmation. Delivery place and date validations are applied against all orders (existing + new).

**Request body:**
```json
{
  "document_numbers": ["2448"]
}
```

- `document_numbers` (required, min 1) — Additional order document numbers to link

**Response:** `ConfirmationResponse`

**Errors:**
- `404` — Confirmation or orders not found
- `422` — Order already linked to a different confirmation, delivery date in the past, or orders span different months

---

### Update Confirmation Status

**PATCH** `/api/organizations/{organization_id}/confirmations/{confirmation_number}/status`

Updates the status of the confirmation and all its linked orders. When status `3` (shipped) is set, a delivery email is sent automatically with NuevoReporte Excel attachments.

**Request body:**
```json
{
  "status": 3
}
```

- `status` (required) — Integer status code (1-5, see table above)

**Email behavior (status = 3):**
- **To:** Configured recipient (env `EMAIL_RECIPIENT`)
- **From:** Configured sender (env `EMAIL_SENDER`)
- **Subject:** `Entrega {delivery_date} {provider_number}`
  - `provider_number` = first 5 digits of supplier internal code, without leading zeros (e.g., `019596262` becomes `19596`)
- **Attachments:** NuevoReporte Excel file for each linked order

**Response:** `ConfirmationResponse`

**Errors:**
- `404` — Confirmation not found
- `422` — Invalid status code

---

### Get Confirmation

**GET** `/api/organizations/{organization_id}/confirmations/{confirmation_number}`

**Response:** `ConfirmationResponse`

**Errors:**
- `404` — Confirmation not found

---

### List Confirmations

**GET** `/api/organizations/{organization_id}/confirmations`

**Query parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number (1-indexed) |
| `pageSize` | int | 12 | Items per page (1-100) |

**Response:** `ConfirmationListResponse`

---

### Remove Order from Confirmation

**DELETE** `/api/organizations/{organization_id}/confirmations/{confirmation_number}/orders/{document_number}`

Unlinks an order from a confirmation (sets `confirmation_id` and `confirmation_number` to null on the order).

**Response:** `ConfirmationResponse` (updated, without the removed order)

**Errors:**
- `404` — Confirmation or order not found
- `422` — Order is not linked to this confirmation

---

## Response Models

### ConfirmationResponse

```json
{
  "confirmation_id": 1,
  "company_id": "ORG-001",
  "confirmation_number": "CONF-001",
  "delivery_date": "15/02/2025",
  "deliver_to_code": "CD01",
  "deliver_to_name": "Centro de Distribucion",
  "confirmation_status": "processing",
  "orders": [
    {
      "order_id": 10,
      "document_number": "2446",
      "delivery_date": "15/02/2025",
      "deliver_to_code": "CD01",
      "deliver_to_name": "Centro de Distribucion",
      "order_status": "processing"
    }
  ]
}
```

### ConfirmationListResponse

```json
{
  "data": [ ...ConfirmationResponse ],
  "pagination": {
    "page": 1,
    "pageSize": 12,
    "totalElements": 25,
    "totalPages": 3
  }
}
```

### OrderResponse Changes

The existing `OrderResponse` now includes two additional fields:

```json
{
  "confirmation_id": 1,
  "confirmation_number": "CONF-001",
  ...rest of existing fields
}
```

These fields are `null` when the order is not linked to any confirmation.

---

## Validation Rules

When linking orders to a confirmation (on create or update):

1. **Same delivery place** — All orders must share the same `deliver_to_code`. The confirmation's `deliver_to_code` and `deliver_to_name` are auto-set from the orders.
2. **No past dates** — Orders with a delivery date before today are rejected.
3. **Same month** — All orders (new + already linked) must share the same month and year. For example, `15/02/2025` and `20/02/2025` is valid, but `15/02/2025` and `01/03/2025` is rejected.
4. **Earliest date wins** — The confirmation's `delivery_date` is automatically set to the earliest delivery date among all linked orders. All orders are updated to this date.
5. **No double-linking** — An order cannot belong to two different confirmations at the same time.

Date format: `dd/mm/yyyy`

---

## Side Effects

When orders are linked to a confirmation (via create or update):

1. Order `delivery_date` is updated in the database
2. **DETALLES Excel** in S3 — "Fecha Entrega" column updated in all rows
3. **Crossdocking Excel** in S3 — "FECHA_ENTREGA" column updated in metadata row
4. Order is **reprocessed** — PDFs and NuevoReporte Excel are regenerated
5. The crossdocking PDF uses `confirmation_number` instead of `bgm011` for the confirmation field
