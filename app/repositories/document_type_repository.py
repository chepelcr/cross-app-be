from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.document_type import DocumentType

logger = logging.getLogger(__name__)


class DocumentTypeRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_id(self, document_type_id: int) -> Optional[DocumentType]:
        try:
            stmt = select(DocumentType).where(
                and_(DocumentType.id == document_type_id, DocumentType.deleted_on.is_(None))
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding document_type {document_type_id}: {e}", exc_info=True)
            raise

    def find_by_code(
        self, code: str, country_code: str = "188"
    ) -> Optional[DocumentType]:
        """Find an active document type by its Hacienda code (e.g. "01", "04").

        Default country_code "188" = Costa Rica (ISO numeric).
        """
        try:
            stmt = select(DocumentType).where(
                and_(
                    DocumentType.code == code,
                    DocumentType.country_code == country_code,
                    DocumentType.status == 1,
                    DocumentType.deleted_on.is_(None),
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding document_type by code {code}/{country_code}: {e}",
                exc_info=True,
            )
            raise

    def find_all_active(self) -> List[DocumentType]:
        try:
            stmt = select(DocumentType).where(
                and_(DocumentType.status == 1, DocumentType.deleted_on.is_(None))
            )
            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error finding active document_types: {e}", exc_info=True)
            raise
