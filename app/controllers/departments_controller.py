from __future__ import annotations

from typing import Annotated, Optional

from fastapi import FastAPI, HTTPException, Path, Query

from app.dtos.requests.department_request_dto import CreateDepartmentDTO, UpdateDepartmentDTO
from app.dtos.responses.department_dto import DepartmentListResponse, DepartmentResponse
from app.services import department_service


class DepartmentsController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/api/organizations/{organization_id}/clients/{client_id}/departments",
            response_model=DepartmentListResponse,
            tags=["departments"],
            summary="Get all departments for a client",
            description="""Get a paginated list of departments with optional search filters.

**Search filters**
- `departmentCode`: Department code
- `name`: Department name (supports wildcards)
- `supplierCode`: Supplier code

**Sorting**
- `orderBy>field` (Ascending)
- `orderBy<field` (Descending)
- Sortable fields: `departmentCode`, `name`, `supplierCode`, `createdOn`, `updatedOn`

**Example:** `name:*warehouse*,orderBy>name`
""",
        )
        async def list_departments(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            client_id: Annotated[str, Path(description="Client UUID")],
            search: Optional[str] = Query(
                None,
                description=(
                    "Search filter string. Syntax: field:value,field2:value2. "
                    "Supports operators: : (equal), ! (not equal), > (greater), < (less), ~ (like). "
                    "Example: name:*warehouse*,orderBy>name"
                ),
            ),
            page: int = Query(1, ge=1, description="Page number (1-indexed)"),
            pageSize: int = Query(12, ge=1, le=100, description="Items per page"),
        ):
            try:
                return department_service.get_departments(
                    organization_id, client_id, page, pageSize, search
                )
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/organizations/{organization_id}/clients/{client_id}/departments/{department_id}",
            response_model=DepartmentResponse,
            tags=["departments"],
            summary="Get a specific department by ID",
        )
        async def get_department(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            client_id: Annotated[str, Path(description="Client UUID")],
            department_id: Annotated[str, Path(description="Department UUID")],
        ):
            try:
                import uuid as uuid_mod

                result = department_service.get_department(uuid_mod.UUID(department_id))
                if not result:
                    raise HTTPException(status_code=404, detail="Department not found")
                return result
            except HTTPException:
                raise
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid department ID format")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post(
            "/api/organizations/{organization_id}/clients/{client_id}/departments",
            response_model=DepartmentResponse,
            tags=["departments"],
            summary="Create a new department",
            status_code=201,
        )
        async def create_department(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            client_id: Annotated[str, Path(description="Client UUID")],
            body: CreateDepartmentDTO,
        ):
            try:
                return department_service.create_department(
                    organization_id, client_id, body
                )
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.put(
            "/api/organizations/{organization_id}/clients/{client_id}/departments/{department_id}",
            response_model=DepartmentResponse,
            tags=["departments"],
            summary="Update an existing department",
        )
        async def update_department(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            client_id: Annotated[str, Path(description="Client UUID")],
            department_id: Annotated[str, Path(description="Department UUID")],
            body: UpdateDepartmentDTO,
        ):
            try:
                result = department_service.update_department(department_id, body)
                if not result:
                    raise HTTPException(status_code=404, detail="Department not found")
                return result
            except HTTPException:
                raise
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid department ID format")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.delete(
            "/api/organizations/{organization_id}/clients/{client_id}/departments/{department_id}",
            tags=["departments"],
            summary="Soft delete a department",
            status_code=204,
        )
        async def delete_department(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            client_id: Annotated[str, Path(description="Client UUID")],
            department_id: Annotated[str, Path(description="Department UUID")],
        ):
            try:
                deleted = department_service.delete_department(department_id)
                if not deleted:
                    raise HTTPException(status_code=404, detail="Department not found")
                return None
            except HTTPException:
                raise
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid department ID format")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
