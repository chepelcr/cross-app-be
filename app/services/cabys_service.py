"""CABYS read-only access.

The `cabys` table is owned by data-services (`consumer-cabys` lambda) — its
search/import endpoints upsert rows from the Hacienda API. cross-app-be only
reads from it; products reference rows by UUID via Product.cabys_id, and the
FK constraint guarantees the row exists.

The previous `get_or_create_cabys` upsert was removed because it wrote to a
table whose schema cross-app-be does not own, leaving every row inserted by
the search path with NULL legacy fields — see migration
`drop_legacy_cabys_name_type`.
"""

from __future__ import annotations

import logging
import uuid as _uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.dtos.responses.product_dto import CabysResponse
from app.models.cabys import Cabys
from app.repositories.cabys_repository import CabysRepository

logger = logging.getLogger(__name__)


def get_by_id(cabys_id: str, session: Optional[Session] = None) -> Optional[CabysResponse]:
    """Return a CABYS entry by UUID, or None if not found."""
    try:
        uid = _uuid.UUID(cabys_id)
    except (TypeError, ValueError):
        return None

    if session is not None:
        repo = CabysRepository.from_session(session)
        cabys = repo.find_by_id(uid)
        return _map_cabys(cabys) if cabys else None

    with CabysRepository() as repo:
        cabys = repo.find_by_id(uid)
        return _map_cabys(cabys) if cabys else None


def get_by_code(code: str) -> Optional[CabysResponse]:
    """Return a CABYS entry by 13-digit code, or None if not found."""
    with CabysRepository() as repo:
        cabys = repo.find_by_code(code)
        return _map_cabys(cabys) if cabys else None


def _map_cabys(cabys: Cabys) -> CabysResponse:
    return CabysResponse(
        id=str(cabys.id),
        code=cabys.code,
        description=cabys.description,
        product_type_id=cabys.product_type_id,
        tax_rate_id=cabys.tax_rate_id,
        country_code=cabys.country_code,
    )
