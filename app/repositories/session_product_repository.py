from __future__ import annotations

from typing import List
import uuid

from sqlalchemy import select

from app.configuration.database_connection import DatabaseConnection
from app.models.session_product import SessionProduct


class SessionProductRepository(DatabaseConnection):
    """Repository for SessionProduct operations."""

    def __init__(self):
        super().__init__()

    def find_by_session(self, session_id: str) -> List[SessionProduct]:
        """Get all products for a session."""
        stmt = select(SessionProduct).where(SessionProduct.session_id == uuid.UUID(session_id))
        return list(self.session.execute(stmt).scalars().all())

    def delete_by_session(self, session_id: str) -> int:
        """Delete all products for a session. Returns count of deleted records."""
        products = self.find_by_session(session_id)
        count = len(products)
        for product in products:
            self.session.delete(product)
        self.session.flush()
        return count

    def bulk_create(
        self, session_id: str, organization_id: str, product_ids: List[str]
    ) -> List[SessionProduct]:
        """Create multiple session products at once."""
        session_products = []
        for product_id in product_ids:
            sp = SessionProduct(
                session_id=uuid.UUID(session_id),
                product_id=product_id,
                organization_id=organization_id,
            )
            self.session.add(sp)
            session_products.append(sp)
        self.session.flush()
        return session_products
