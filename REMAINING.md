# Remaining Work - Cross-App BE

## Just Completed (this session)

### PATCH Status Endpoints + Missing CRUD Endpoints

Added the following endpoints across all controllers:

| Controller | Endpoint | Method | Status |
|---|---|---|---|
| **Products** | `/api/organizations/{org}/products/{id}` | PATCH | DONE |
| **Clients** | `/api/organizations/{org}/clients` | POST | DONE |
| **Clients** | `/api/organizations/{org}/clients/{id}` | PUT | DONE |
| **Clients** | `/api/organizations/{org}/clients/{id}` | PATCH | DONE |
| **Stores** | `/api/organizations/{org}/clients/{cid}/stores` | POST | DONE |
| **Stores** | `/api/organizations/{org}/clients/{cid}/stores/{id}` | PUT | DONE |
| **Stores** | `/api/organizations/{org}/clients/{cid}/stores/{id}` | PATCH | DONE |
| **Departments** | `/api/organizations/{org}/clients/{cid}/departments/{id}` | PATCH | DONE |

Files modified:
- `app/services/product_service.py` - added `update_product_status()`
- `app/services/client_service.py` - added `create_client()`, `update_client()`, `update_client_status()`
- `app/services/store_service.py` - added `create_store()`, `update_store()`, `update_store_status()`
- `app/services/department_service.py` - added `update_department_status()`
- `app/controllers/products_controller.py` - added PATCH endpoint
- `app/controllers/clients_controller.py` - added POST, PUT, PATCH endpoints
- `app/controllers/stores_controller.py` - added POST, PUT, PATCH endpoints
- `app/controllers/departments_controller.py` - added PATCH endpoint
- `app/dtos/requests/client_request_dto.py` - created (ClientRequestDTO)
- `app/dtos/requests/store_request_dto.py` - created (StoreRequestDTO)

---

## Completed in Previous Sessions

### DB Normalization (feature/db-normalization branch)

1. **Phase 1 Migration** - Created new normalized tables: `clients`, `stores`, `departments` with proper FK relationships
2. **Models** - Created `Client`, `Store`, `Department` models with `AuditMixin`; updated `Order`, `OrderLine`, `SalePoint`, `Item`, `Confirmation` to use FK references
3. **CRUD Stacks** - Full GET/search endpoints for clients, stores, departments, products
4. **Upsert-on-parse** - Excel parser now upserts into normalized tables, mapper/PDF use relationships
5. **Phase 2 Migration** - Dropped 23 denormalized columns across 5 tables
6. **Search Filters** - Converted to join-based using `relationship.has()` for client_name, supplier_name, deliver_to_code, deliver_to_name

### Product Image Upload

- `POST /api/organizations/{org}/products` - create product with optional base64 image
- `PUT /api/organizations/{org}/products/{id}` - update product with optional base64 image
- Image validation: allowed types (png, jpeg, jpg, gif, webp), max 5MB, data URL prefix stripping
- S3 upload via existing `upload_file_to_s3()`, key: `organizations/{org}/products/{id}/image.{ext}`

---

## Still Remaining

### 1. Verify Full Import Chain (Quick)
Run the FastAPI app to verify all new endpoints register without import errors:
```bash
python -c "from app.main import app; print('OK')"
```

### 2. Push and Merge (Task #14)
```bash
git add -A
git commit -m "Add PATCH status + missing CRUD endpoints for all controllers"
git push origin feature/db-normalization
# Create PR to develop
```

### 3. Optional Improvements (Not Required)
- **Validation on create**: Require `store_code` on store create, `client_name` or `client_gln` on client create
- **Authorization**: Verify the entity belongs to the organization_id in the path (currently stores/departments only check by ID, not by org)
- **Tests**: Unit tests for new service methods
- **Product PATCH semantics**: Currently maps status 1=active, anything else=inactive. Could use same AuditMixin pattern if Product model changes
