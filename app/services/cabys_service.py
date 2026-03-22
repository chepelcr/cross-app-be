from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.cabys import Cabys
from app.dtos.responses.product_dto import CabysResponse
from app.repositories.cabys_repository import CabysRepository

logger = logging.getLogger(__name__)


def get_cabys_by_code(code: str) -> Optional[CabysResponse]:
    """Return a CABYS entry by code, or None if not found."""
    with CabysRepository() as repo:
        cabys = repo.find_by_code(code)
        if not cabys:
            return None
        return _map_cabys(cabys)


def get_or_create_cabys(
    code: str,
    name: str,
    type_: int,
    session: Optional[Session] = None,
) -> CabysResponse:
    """Upsert a CABYS entry.  When *session* is provided, the operation shares
    the caller's transaction (no new context manager is opened).
    """
    if session is not None:
        repo = CabysRepository.from_session(session)
        cabys = repo.find_or_create(code, name, type_)
        return _map_cabys(cabys)

    with CabysRepository() as repo:
        cabys = repo.find_or_create(code, name, type_)
        return _map_cabys(cabys)


def _map_cabys(cabys: Cabys) -> CabysResponse:
    return CabysResponse(
        id=str(cabys.id),
        code=cabys.code,
        name=cabys.name,
        type=cabys.type,
    )
