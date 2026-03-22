# FE Integration: Crossdocking Report Color Scheme

## Overview

Crossdocking reports (PDF + NuevoReporte Excel) now support four color schemes.
The selected color is stored per order and reused on reprocess unless overridden.

**Default colors by department (when no color is sent):**

| Department code | Default color |
|-----------------|---------------|
| `22`            | `orange`      |
| `26`            | `green_alt`   |
| Any other       | `green`       |

---

## Color Schemes

| Value       | Label        | Primary (headers)                                           | Light rows                                                   |
|-------------|--------------|-------------------------------------------------------------|--------------------------------------------------------------|
| `green`     | Verde        | ![#0e5c23](https://placehold.co/14x14/0e5c23/0e5c23.png) `#0e5c23` | ![#d4edda](https://placehold.co/14x14/d4edda/d4edda.png) `#d4edda` |
| `orange`    | Naranja      | ![#c65811](https://placehold.co/14x14/c65811/c65811.png) `#c65811` | ![#f7caad](https://placehold.co/14x14/f7caad/f7caad.png) `#f7caad` |
| `blue`      | Azul         | ![#1e4e77](https://placehold.co/14x14/1e4e77/1e4e77.png) `#1e4e77` | ![#9ac1e6](https://placehold.co/14x14/9ac1e6/9ac1e6.png) `#9ac1e6` |
| `green_alt` | Verde Claro  | ![#375522](https://placehold.co/14x14/375522/375522.png) `#375522` | ![#a9d08d](https://placehold.co/14x14/a9d08d/a9d08d.png) `#a9d08d` |

---

## API Changes

### 1. Parse Crossdocking Excel

**Endpoint:** `POST /api/organizations/{organization_id}/orders/{document_number}/crossdocking/parse`

Added optional `color` field to the existing request body.

**Request body (before):**
```json
{
  "data": "<base64>",
  "name": "file.xlsx",
  "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}
```

**Request body (after):**
```json
{
  "data": "<base64>",
  "name": "file.xlsx",
  "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "color": "orange"
}
```

- `color` is optional. Omitting it applies the department-based default (see table above).
- Valid values: `"green"`, `"orange"`, `"blue"`, `"green_alt"`.

---

### 2. Reprocess Order

**Endpoint:** `POST /api/organizations/{organization_id}/orders/{document_number}/reprocess`

Now accepts an optional JSON body (previously no body).

**Request body:**
```json
{
  "color": "blue"
}
```

- Omit the body entirely (or send `{}`) to reprocess using the **stored color** from the previous upload.
- Send `color` to override the stored color for this and future reprocesses.

---

### 3. Order Response — new field

All order responses now include `report_color`:

```json
{
  "order_id": 123,
  "document_number": "PO-2446",
  "report_color": "orange",
  ...
}
```

Use this to pre-select the correct color in any color-picker UI on the order detail page.

---

## Suggested UI Changes

### A. Upload crossdocking dialog

Add a color selector (radio buttons or segmented control) before the upload button.
Pre-select the department default (resolve it client-side using the order's department code or just leave it blank to let the API decide).

```
Color del reporte:
  ○ Verde       ● Naranja   ○ Azul   ○ Verde Claro
  [Subir archivo]
```

Render each option as a colored swatch using the primary hex values from the table above.

### B. Reprocess dialog / button

If the order already has `report_color`, pre-select that value.
Allow changing it before confirming the reprocess.

```
Reprocesar orden PO-2446
Color del reporte: [Verde Claro ▾]
[Reprocesar]
```

### C. Order detail / badge

Show a small color chip next to the order to indicate which scheme was used:

```jsx
<span style={{ background: colorHex, width: 12, height: 12, borderRadius: 2 }} />
```

Mapping for the chip color (`hdr_dark` hex):

```js
const SCHEME_COLOR = {
  green:     '#0e5c23',
  orange:    '#c65811',
  blue:      '#1e4e77',
  green_alt: '#375522',
};
```

---

## TypeScript Types

```ts
export type ReportColorScheme = 'green' | 'orange' | 'blue' | 'green_alt';

export interface CrossdockingParseRequest {
  data: string;          // base64
  name: string;
  content_type: string;
  color?: ReportColorScheme;
}

export interface SelectColorRequest {
  color?: ReportColorScheme;
}

export const REPORT_COLOR_OPTIONS: { value: ReportColorScheme; label: string; hex: string }[] = [
  { value: 'green',     label: 'Verde',       hex: '#0e5c23' },
  { value: 'orange',    label: 'Naranja',      hex: '#c65811' },
  { value: 'blue',      label: 'Azul',         hex: '#1e4e77' },
  { value: 'green_alt', label: 'Verde Claro',  hex: '#375522' },
];
```
