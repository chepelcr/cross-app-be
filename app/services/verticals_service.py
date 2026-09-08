from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import joinedload

from app.configuration.database_connection import DatabaseConnection
from app.models.client_asset import ClientAsset
from app.models.verticals import (
    Appointment,
    CommissionRule,
    ControlledSale,
    PriceSchedule,
    PriceScheduleItem,
    ProductLot,
    ProductUnit,
    RecurringInvoice,
)

logger = logging.getLogger(__name__)


class VerticalsRepository(DatabaseConnection):
    """Read/write access for the vertical tables.

    Grouped rather than one repository per table: they share no joins, and ten
    near-identical files would be harder to keep consistent than one.
    """

    def __init__(self):
        super().__init__()

    def _org_rows(self, model, organization_id: str, order_by=None):
        stmt = select(model).where(
            and_(model.organization_id == organization_id, model.deleted_on.is_(None))
        )
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        return list(self.session.execute(stmt).unique().scalars().all())

    def price_schedules(self, organization_id: str) -> List[PriceSchedule]:
        stmt = (
            select(PriceSchedule)
            .options(joinedload(PriceSchedule.items))
            .where(
                and_(
                    PriceSchedule.organization_id == organization_id,
                    PriceSchedule.deleted_on.is_(None),
                )
            )
            .order_by(PriceSchedule.priority.desc())
        )
        return list(self.session.execute(stmt).unique().scalars().all())

    def lots_for_product(self, organization_id: str, product_id: str) -> List[ProductLot]:
        stmt = select(ProductLot).where(
            and_(
                ProductLot.organization_id == organization_id,
                ProductLot.product_id == product_id,
                ProductLot.deleted_on.is_(None),
            )
        )
        return list(self.session.execute(stmt).scalars().all())

    def units_for_product(self, product_id: str) -> List[ProductUnit]:
        stmt = select(ProductUnit).where(
            and_(ProductUnit.product_id == product_id, ProductUnit.deleted_on.is_(None))
        )
        return list(self.session.execute(stmt).scalars().all())

    def commission_rules(self, organization_id: str) -> List[CommissionRule]:
        return self._org_rows(CommissionRule, organization_id)

    def appointments_in_range(
        self, organization_id: str, start: datetime, end: datetime
    ) -> List[Appointment]:
        stmt = (
            select(Appointment)
            .where(
                and_(
                    Appointment.organization_id == organization_id,
                    Appointment.deleted_on.is_(None),
                    Appointment.starts_at >= start,
                    Appointment.starts_at <= end,
                )
            )
            .order_by(Appointment.starts_at)
        )
        return list(self.session.execute(stmt).scalars().all())

    def assets_for_client(self, organization_id: str, client_id: uuid.UUID) -> List[ClientAsset]:
        stmt = (
            select(ClientAsset)
            .where(
                and_(
                    ClientAsset.organization_id == organization_id,
                    ClientAsset.client_id == client_id,
                    ClientAsset.deleted_on.is_(None),
                )
            )
            .order_by(ClientAsset.identifier)
        )
        return list(self.session.execute(stmt).scalars().all())

    def due_recurring(self, organization_id: str) -> List[RecurringInvoice]:
        return self._org_rows(RecurringInvoice, organization_id)

    def save(self, entity):
        self.session.add(entity)
        self.session.flush()
        self.session.refresh(entity)
        return entity
