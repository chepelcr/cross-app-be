# Backend Changes Required for Product Module

## Database Schema Changes

### Products Table

Add new columns to support complete product structure:

```sql
-- Cabys lookup table (normalized, no repeated data per product)
CREATE TABLE cabys (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code       VARCHAR(13) NOT NULL UNIQUE,
  name       TEXT        NOT NULL,
  type       INTEGER     NOT NULL
);

-- Fiscal Information
ALTER TABLE products ADD COLUMN cabys_id UUID REFERENCES cabys(id);
ALTER TABLE products ADD COLUMN unit_id INTEGER DEFAULT 85;
ALTER TABLE products ADD COLUMN commercial_unit_measure VARCHAR(50);

-- Packaging
ALTER TABLE products ADD COLUMN is_packaged BOOLEAN DEFAULT FALSE;
ALTER TABLE products ADD COLUMN quantity DECIMAL(10,3) DEFAULT 1;
ALTER TABLE products ADD COLUMN unit_price DECIMAL(10,5);

-- Customs
ALTER TABLE products ADD COLUMN customs_part VARCHAR(50);

-- Complex fields (JSON)
ALTER TABLE products ADD COLUMN codes JSONB DEFAULT '[]';
ALTER TABLE products ADD COLUMN discounts JSONB DEFAULT '[]';
ALTER TABLE products ADD COLUMN taxes JSONB DEFAULT '[]';

-- Calculated values
ALTER TABLE products ADD COLUMN original_price DECIMAL(10,5); -- Rename from netPrice
ALTER TABLE products ADD COLUMN base_amount DECIMAL(10,5);
ALTER TABLE products ADD COLUMN sale_price DECIMAL(10,5);

-- Remove old price field or rename it
-- Keep existing 'price' field as the original product price
```

> Catalog table schemas and identifier strategy: see [CATALOGS.md](./CATALOGS.md).

## JSON Structure Definitions

### ProductCode Structure
```json
{
  "codeTypeId": "01",
  "number": "ABC123",
  "description": "Internal code"
}
```
> `codeTypeId` is the Hacienda catalog `code` value (e.g. `"01"`), not a UUID.

### ProductDiscount Structure
```json
{
   "discountTypeId": "01",
   "percentage": 10.0,
   "amount": 1000.0,
   "reason": "Volume discount",
   "isAmount": false
}
```
> `discountTypeId` is the Hacienda catalog `code` value (e.g. `"01"`), not a UUID.

**Discount Calculation Logic:**
- If `isAmount = true`: Use `amount` as fixed discount value
- If `isAmount = false`: Calculate discount as `originalPrice * percentage / 100`
- Either `percentage` or `amount` must be provided (not both required)

### ProductTax Structure
```json
{
  "taxTypeId": "01",
  "amount": 1300.0,
  "taxRate": { "id": "08", "percentage": 13.0 },
  "taxFactor": null,
  "otherTaxType": null,
  "specialFields": {
    "quantity": 10.0,
    "percentage": 13.0,
    "proportion": 0.5,
    "volumeConsumption": 100.0,
    "taxAmount": { "id": "550e8400-e29b-41d4-a716-446655440000", "amount": 1300.0 }
  },
  "isAmount": false
}
```
> `taxTypeId` is the Hacienda `code` value (e.g. `"01"`), not a UUID.
> `taxRate.id` is the Hacienda `code` of the rate (e.g. `"08"`). `taxFactor` and `taxAmount` use real UUIDs as `id`.
> See [CATALOGS.md](./CATALOGS.md) for full identifier strategy.

**Tax Calculation Logic:**
- IVA (code 01, 07, 08): `baseAmount * taxRate.percentage / 100`
- Special taxes (code 02-06, 12): Use `specialFields.taxAmount` for complex calculations
- Others (code 99): `baseAmount * taxRate.percentage / 100`
- `specialFields` with `taxAmount` required for: IUC (03), ISEBA (04), ISEBEC (05), IPT (06)

## API Endpoints Changes

### GET /products/:id
**Response should include:**
```json
{
  "id": "uuid",
  "name": "Product Name",
  "description": "Description",
  "price": 10000.00,
  "categoryId": "uuid",
  "imageUrl": "url",
  "isActive": true,
  "sku": "SKU123",
  "stockQuantity": 100,
  "lowStockThreshold": 10,
  "trackInventory": true,
  "unitsPerBox": 12,
  "cabys": {
    "id": "uuid",
    "code": "1234567890123",
    "name": "Product CABYS description",
    "type": 1
  },
  "unitId": 85,
  "commercialUnitMeasure": "Unidad",
  "isPackaged": false,
  "quantity": 1,
  "unitPrice": 10000.00,
  "customsPart": "1234.56.78",
  "codes": [
    {
      "codeTypeId": "01",
      "number": "ABC123",
      "description": "Internal code"
    }
  ],
  "discounts": [
    {
      "discountTypeId": "01",
      "percentage": 10.0,
      "amount": null,
      "reason": null,
      "isAmount": false
    }
  ],
  "taxes": [
    {
      "taxTypeId": "01",
      "amount": null,
      "taxRate": { "id": "08", "percentage": 13.0 },
      "taxFactor": null,
      "otherTaxType": null,
      "specialFields": null,
      "isAmount": false
    }
  ],
  "baseAmount": 9000.00,
  "salePrice": 10170.00,
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z"
}
```

### POST /products
### PUT /products/:id
**Request body should accept all fields above**

## Calculation Flow (Backend)

### Product Calculations
```
1. price = base product price (user input)
2. totalAmount = price * quantity (for packaged products)
3. discountAmount = sum of all discount amounts
   - If discount.isAmount: use discount.amount
   - Else: price * discount.percentage / 100
4. subtotal = totalAmount - discountAmount
5. baseAmount = subtotal (or manual input for IVACE tax code 07)
6. Process special taxes (ISC-02, IUC-03, ISEBA-04, ISEBEC-05, IPT-06, ISEC-12):
   - Calculate tax amount
   - Add to netTax and totalAmountLine
   - For taxes with for_base_amount=true (ISC, ISEBA, ISEBEC, ISEC): baseAmount += taxAmount
7. Process OTHERS taxes (code 99):
   - Calculate: baseAmount * taxRate.percentage / 100
   - Add to netTax and totalAmountLine
8. Process IVA taxes (IVA-01, IVACE-07, IVARBU-08):
   - IVA/IVACE: baseAmount * taxRate.percentage / 100
   - IVARBU: taxFactor.factor * subtotal
   - Add to netTax and totalAmountLine
9. salePrice = totalAmountLine
```

### Tax Processing Order (CRITICAL)
**Must process in this exact order:**
1. Special taxes first (they may add to baseAmount)
2. OTHERS taxes second (use accumulated baseAmount)
3. IVA taxes last (use final baseAmount)

### Special Tax Calculations

#### IUC (03) - Impuesto Único a los Combustibles
```
amount = specialFields.quantity * specialFields.taxAmount.amount
```
- `quantity`: Cantidad de la unidad de medida a utilizar
- `taxAmount.amount`: Impuesto por Unidad (from taxAmount DTO)

#### ISEBA (04) - Impuesto Específico de Bebidas Alcohólicas
```
proportion = specialFields.quantity * specialFields.percentage / 100
amount = detailQuantity * proportion * specialFields.taxAmount.amount
```
- `quantity`: Cantidad de la unidad de medida a utilizar
- `percentage`: Porcentaje
- `proportion`: Calculated field (quantity * percentage / 100)
- `taxAmount.amount`: Impuesto por Unidad (from taxAmount DTO)
- `detailQuantity`: Product quantity from detail line

#### ISEBEC (05) - Impuesto Específico sobre Bebidas Envasadas
**For non-alcoholic beverages (CABYS starts with '2202'):**
```
altAmount = specialFields.taxAmount.amount / specialFields.volumeConsumption
amount = detailQuantity * specialFields.quantity * altAmount
```

**For other products:**
```
amount = specialFields.quantity * specialFields.volumeConsumption * specialFields.taxAmount.amount
```
- `quantity`: Cantidad de la unidad de medida a utilizar
- `volumeConsumption`: Volumen por Unidad de Consumo
- `taxAmount.amount`: Impuesto por Unidad (from taxAmount DTO)
- `detailQuantity`: Product quantity from detail line

#### IPT (06) - Impuesto a los Productos de Tabaco
```
amount = detailQuantity * specialFields.quantity * specialFields.taxAmount.amount
```
- `quantity`: Cantidad de la unidad de medida a utilizar
- `taxAmount.amount`: Impuesto por Unidad (from taxAmount DTO)
- `detailQuantity`: Product quantity from detail line

#### ISC (02) - Impuesto Selectivo de Consumo
```
amount = subtotal * taxRate.percentage / 100
```
- Uses `taxRate.percentage`; `taxRate.id` is null (no catalog entry)
- Adds to baseAmount

#### ISEC (12) - Impuesto Específico al Cemento
```
amount = subtotal * taxRate.percentage / 100
```
- Fixed rate: 5.0%; `taxRate.id` is null (no catalog entry)
- Adds to baseAmount

#### OTHERS (99) - Otros Impuestos
```
amount = baseAmount * taxRate.percentage / 100
```
- Uses accumulated baseAmount (after special taxes)

#### IVA (01) - Impuesto al Valor Agregado
```
amount = baseAmount * taxRate.percentage / 100
```
- Uses final baseAmount (after all special taxes)

#### IVACE (07) - IVA Cálculo Especial
```
amount = baseAmount * taxRate.percentage / 100
```
- `baseAmount` is manually provided (not calculated)
- User must input baseAmount when using IVACE

#### IVARBU (08) - IVA Régimen de Bienes Usados
```
amount = taxFactor.factor * subtotal
```
- Uses `taxFactor.factor` instead of a rate
- `taxFactor` DTO `{ id, factor }` is required

### Base Amount Accumulation
These tax types add their amount to baseAmount:
- **02 (ISC)**: Impuesto Selectivo de Consumo
- **04 (ISEBA)**: Impuesto Específico de Bebidas Alcohólicas  
- **05 (ISEBEC)**: Impuesto Específico sobre Bebidas Envasadas
- **12 (ISEC)**: Impuesto Específico al Cemento

This ensures IVA is calculated on: `subtotal + special_taxes_amount`

### Validation Rules

**Discounts:**
- Maximum 5 discounts per product
- Total discount percentage cannot exceed 100%
- Either `percentage` or `amount` must be provided
- If `discountTypeId = 99` (Other), `reason` is required (min 5 characters)

**Taxes:**
- `taxRate` is required unless `specialFields` is provided
- IVA taxes (codes 01, 07, 08) require `taxRate` with a valid `id` (Hacienda code)
- Special taxes (codes 03-06) require `specialFields` with `taxAmount`
- IVARBU (code 08) requires `taxFactor`
- Code 99 (Others) requires `otherTaxType` description
- **Tax processing order matters**: Special taxes → OTHERS → IVA
- Special taxes with `for_base_amount=true` (02, 04, 05, 12) add their amount to baseAmount before IVA calculation

**CABYS:**
- Must be exactly 13 digits
- Required for tax calculations
- Should validate against Hacienda API

**Packaging:**
- If `isPackaged = true`, `quantity` and `unitPrice` are required
- `price` is calculated as `quantity * unitPrice` for packaged products

## Migration Script Example

```sql
-- Step 0: Create cabys table
CREATE TABLE IF NOT EXISTS cabys (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(13) NOT NULL UNIQUE,
  name  TEXT        NOT NULL,
  type  INTEGER     NOT NULL
);

-- Step 1: Add new columns
ALTER TABLE products
  ADD COLUMN cabys_id UUID REFERENCES cabys(id),
  ADD COLUMN unit_id INTEGER DEFAULT 85,
  ADD COLUMN commercial_unit_measure VARCHAR(50),
  ADD COLUMN is_packaged BOOLEAN DEFAULT FALSE,
  ADD COLUMN quantity DECIMAL(10,3) DEFAULT 1,
  ADD COLUMN unit_price DECIMAL(10,5),
  ADD COLUMN customs_part VARCHAR(50),
  ADD COLUMN codes JSONB DEFAULT '[]',
  ADD COLUMN discounts JSONB DEFAULT '[]',
  ADD COLUMN taxes JSONB DEFAULT '[]',
  ADD COLUMN base_amount DECIMAL(10,5),
  ADD COLUMN sale_price DECIMAL(10,5);

-- Step 2: Update existing products with default values
UPDATE products
SET
  unit_id = 85,
  is_packaged = FALSE,
  quantity = 1,
  codes = '[]',
  discounts = '[]',
  taxes = '[]'
WHERE unit_id IS NULL;

-- Step 4: Calculate initial sale_price from original_price
UPDATE products 
SET sale_price = price 
WHERE sale_price IS NULL;
```

## TypeScript Types (Backend Reference)

```typescript
interface Cabys {
  id: string;
  code: string;  // 13-digit CABYS code
  name: string;
  type: number;
}

interface ProductCode {
  codeTypeId: string;  // Hacienda code (e.g. "01") — lookup by code_types.code, not UUID
  number: string;
  description?: string;
}

interface ProductDiscount {
  discountTypeId: string;  // Hacienda code (e.g. "01") — lookup by discount_types.code, not UUID
  percentage?: number;
  amount?: number;
  reason?: string;
  isAmount?: boolean;
}

interface TaxSpecialFields {
  quantity?: number;
  percentage?: number;      // Used in ISEBA proportion calculation (not a tax rate)
  proportion?: number;      // Calculated: quantity * percentage / 100
  volumeConsumption?: number;
  taxAmount?: TaxAmountDto; // Replaces taxAmountId + taxUnitAmount — see CATALOGS.md
}

interface ProductTax {
  taxTypeId: string;          // Hacienda code (e.g. "01") — lookup by tax_types.code
  amount?: number;            // Calculated tax amount (output)
  taxRate?: TaxRateDto;       // Replaces taxRateId + rate — id is Hacienda code or null
  taxFactor?: TaxFactorDto;   // Replaces taxFactorId + factor — IVARBU only
  otherTaxType?: string;
  specialFields?: TaxSpecialFields;
  isAmount?: boolean;
}

// DTOs defined in CATALOGS.md:
// interface TaxRateDto   { id: string | null; percentage: number; }
// interface TaxFactorDto { id: string; factor: number; }
// interface TaxAmountDto { id: string; amount: number; }

interface Product {
  id: string;
  name: string;
  description: string;
  price: number; // Base product price
  categoryId: string;
  imageUrl: string | null;
  isActive: boolean;
  sku?: string | null;
  stockQuantity?: number;
  lowStockThreshold?: number;
  trackInventory?: boolean;
  unitsPerBox?: number | null;
  cabys?: Cabys | null;  // type comes from cabys.type — no separate productTypeId needed
  unitId?: number;
  commercialUnitMeasure?: string | null;
  isPackaged?: boolean;
  quantity?: number;
  unitPrice?: number;
  customsPart?: string | null;
  codes?: ProductCode[];
  discounts?: ProductDiscount[];
  taxes?: ProductTax[];
  baseAmount?: number;
  salePrice?: number;
  createdAt: Date;
  updatedAt: Date;
}
```

## Notes

1. **price field**: Keep existing `price` field as the base product price before any calculations.

2. **Calculation Order**: Always calculate in this order:
   - price (base)
   - Apply discounts → subtotal
   - Calculate baseAmount (subtotal or manual for IVACE)
   - Apply taxes → salePrice

3. **JSONB Fields**: Use PostgreSQL JSONB for flexible storage of codes, discounts, and taxes arrays.

4. **Backward Compatibility**: Existing `price` field is used as the base price for all calculations.

5. **Frontend Integration**: Frontend already implements these structures and calculations. Backend needs to match.

6. **CABYS normalized to separate table**: `cabys` and `cabysDescription` flat columns are replaced by a `cabys_id` FK referencing the `cabys` table (`id`, `code`, `name`, `type`). The API response returns the full `cabys` object, not individual fields. `productTypeId` is removed from `Product` — use `cabys.type` instead. Populate `cabys` from the Hacienda catalog before migrating existing product data.

7. **Redundant code fields removed**: `internalCode`, `originalCode`, and `clientArticleCode` are consolidated into the `codes` JSONB array. Remove these columns from the products table after migrating their data into the `codes` array with the appropriate `codeTypeId`.

8. **Catalog DTOs and identifier strategy**: `taxRate`, `taxFactor`, and `taxAmount` are embedded DTO objects in the product tax payload so the backend has all values required for calculations without additional catalog lookups. Full schemas, identifier strategy, and seeding notes are in [CATALOGS.md](./CATALOGS.md).
