from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.organization import Organization

logger = logging.getLogger(__name__)


class OrganizationRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_id(self, organization_id: str) -> Optional[Organization]:
        try:
            stmt = select(Organization).where(Organization.id == organization_id)
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding organization {organization_id}: {e}", exc_info=True)
            raise

    def upsert(
        self,
        organization_id: str,
        name: str = None,
        slug: str = None,
        gln: str = None,
        internal_code: str = None,
        logo_url: str = None,
        owner_id: str = None,
    ) -> Organization:
        try:
            org = self.find_by_id(organization_id)
            if not org:
                # Create a minimal org record so FK constraints are satisfied
                org = Organization(
                    id=organization_id,
                    name=name or organization_id,
                    slug=slug or organization_id,
                    owner_id=owner_id or "system",
                    plan="free",
                    is_active=True,
                )
                self.session.add(org)
                logger.info(f"Created organization record for {organization_id}")

            if name is not None:
                org.name = name
            if gln is not None:
                org.gln = gln
            if internal_code is not None:
                org.internal_code = internal_code
            if logo_url is not None:
                org.logo_url = logo_url
            self.session.flush()
            return org
        except SQLAlchemyError as e:
            logger.error(f"Error upserting organization {organization_id}: {e}", exc_info=True)
            raise
