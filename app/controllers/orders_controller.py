from typing import Annotated, Optional

from fastapi import Body, FastAPI, HTTPException, Path, Query

from app.dtos.files import ExcelDTO, ExcelAndColorDTO
from app.dtos import OrderListResponse, OrderResponse, SelectColorDTO
from app.dtos.requests.status_request_dto import StatusRequestDTO
from app.services import order_service


class OrdersController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):
        @app.post(
            "/api/organizations/{organization_id}/orders/parse",
            response_model=OrderResponse,
            tags=["orders"],
            summary="Parse and save an order details (DETALLES) Excel file",
        )
        async def parse_and_save_order(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            body: ExcelDTO = Body(...),
        ):
            try:
                return order_service.process_order_excel(organization_id, body)
            except ValueError as e:
                raise HTTPException(status_code=409, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=422, detail=str(e))

        @app.post(
            "/api/organizations/{organization_id}/orders/{document_number}/crossdocking/parse",
            response_model=OrderResponse,
            tags=["orders"],
            summary="Parse and save a crossdocking Excel file for an existing order",
        )
        async def parse_and_save_crossdocking(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            document_number: Annotated[str, Path(description="Order document number")],
            body: ExcelAndColorDTO = Body(...),
        ):
            try:
                return order_service.process_crossdocking_excel(
                    organization_id, document_number, body
                )
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post(
            "/api/organizations/{organization_id}/orders/{document_number}/reprocess",
            response_model=OrderResponse,
            tags=["orders"],
            summary="Reprocess order: re-parse Excel files and regenerate all outputs",
        )
        async def reprocess_order(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            document_number: Annotated[str, Path(description="Order document number")],
            body: Optional[SelectColorDTO] = Body(None),
        ):
            try:
                color = body.color if body else None
                return order_service.reprocess_order(organization_id, document_number, color)
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/organizations/{organization_id}/orders",
            response_model=OrderListResponse,
            tags=["orders"],
            summary="Get all orders for an organization",
            description="""Get a paginated list of orders with optional search filters.

**Search operators**
- `:` = Equal
- `!` = Not equal
- `<` = Less than
- `>` = Greater than
- `~` = Like (contains)

**Between (BETWEEN)**
- `field:value1~value2` = Between values (e.g. `deliveryDate:01/02/2025~28/02/2025`)
- `field!value1~value2` = Not between values

**Search filters**
- `documentNumber`: Document number (supports wildcards)
- `clientName`: Client name (supports wildcards)
- `supplierName`: Supplier name (supports wildcards)
- `deliveryDate`: Delivery date — dd/mm/yyyy (supports between)
- `creationDate`: Creation date — dd/mm/yyyy (supports between)
- `orderStatus`: Order status (pending, processing, shipped, delivered, cancelled)
- `deliverToCode`: Delivery place code
- `deliverToName`: Delivery place name (supports wildcards)
- `confirmationNumber`: Confirmation number (supports wildcards)

**Separators**
Filters are individual conditions separated by commas (,).
Logical AND and OR conditions can be applied:
- AND: All conditions separated by commas and outside parentheses are combined with AND
- OR: To apply OR conditions, group them inside parentheses

**Examples**
- `clientName:*corp*,orderStatus:pending` → Orders where client name contains "corp" **and** status is pending
- `(orderStatus:pending,orderStatus:processing)` → Orders with status pending **or** processing
- `clientName:*test*,(orderStatus:pending,orderStatus:shipped)` → Client name contains "test" **and** (status pending **or** shipped)
- `deliveryDate:01/02/2025~28/02/2025` → Orders with delivery date between Feb 1 and Feb 28

**Wildcards**
- `*ana*` = Contains (e.g. `clientName:*ana*` → Ariana, Melania)
- `Al*` = Starts with (e.g. `clientName:Al*` → Alberto, Alana)
- `*el` = Ends with (e.g. `clientName:*el` → Daniel, Miguel)

**Note:** Fields that support wildcards (`documentNumber`, `clientName`, `supplierName`, `deliverToName`, `confirmationNumber`) automatically apply case-insensitive contains matching even without `*` wildcards.

**Sorting**
- `orderBy>field` (Ascending)
- `orderBy<field` (Descending)
- Sortable fields: `documentNumber`, `clientName`, `supplierName`, `deliveryDate`, `creationDate`, `orderStatus`, `createdOn`, `updatedOn`

**Example with sorting:** `orderStatus:pending,orderBy>deliveryDate`
""",
        )
        async def get_orders(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            search: Optional[str] = Query(
                None,
                description=(
                    "Search filter string. Syntax: field:value,field2:value2. "
                    "Supports operators: : (equal), ! (not equal), > (greater), < (less), ~ (like). "
                    "Use () for OR grouping. Example: clientName:*Test*,orderStatus:pending,orderBy>deliveryDate"
                ),
                examples=["orderStatus:pending,orderBy>deliveryDate"],
            ),
            page: int = Query(1, ge=1, description="Page number (1-indexed)"),
            pageSize: int = Query(12, ge=1, le=100, description="Items per page"),
        ):
            return order_service.get_orders(
                organization_id,
                search=search,
                page=page,
                page_size=pageSize,
            )

        @app.get(
            "/api/organizations/{organization_id}/orders/{document_number}",
            response_model=OrderResponse,
            tags=["orders"],
            summary="Get a specific order by document number (includes crossdocking if uploaded)",
        )
        async def get_order_by_number(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            document_number: Annotated[str, Path(description="Order document number")],
        ):
            try:
                return order_service.get_order(organization_id, document_number)
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))

        @app.patch(
            "/api/organizations/{organization_id}/orders/{document_number}",
            response_model=OrderResponse,
            tags=["orders"],
            summary="Update order status",
        )
        async def update_order_status(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            document_number: Annotated[str, Path(description="Order document number")],
            body: StatusRequestDTO = Body(...),
        ):
            try:
                return order_service.update_order_status(organization_id, document_number, body.status)
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
