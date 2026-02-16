from typing import Annotated

from fastapi import Body, FastAPI, HTTPException, Path

from app.dtos import ExcelFileDTO
from app.services import store_slot_service


class StoreSlotsController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.post(
            "/api/organizations/{organization_id}/store-slots/upload",
            tags=["store-slots"],
        )
        async def upload_store_slots(
            organization_id: Annotated[str, Path(...)],
            body: ExcelFileDTO = Body(...),
        ):
            try:
                count = store_slot_service.upload_store_slots(body)
                return {"message": f"Upserted {count} store slots", "count": count}
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
