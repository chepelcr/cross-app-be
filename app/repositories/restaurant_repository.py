from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.configuration.database_connection import DatabaseConnection
from app.models.restaurant import (
    ComboItem,
    KitchenStation,
    Modifier,
    ModifierGroup,
    ProductModifierGroup,
    ProductStation,
)

logger = logging.getLogger(__name__)


class RestaurantRepository(DatabaseConnection):
    """Combos, modifier groups and kitchen stations."""

    def __init__(self):
        super().__init__()

    # ── Combos ───────────────────────────────────────────────────────────
    def find_combo_items(self, combo_product_id: str) -> List[ComboItem]:
        try:
            stmt = (
                select(ComboItem)
                .where(ComboItem.combo_product_id == combo_product_id)
                .order_by(ComboItem.sort_order)
            )
            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error loading combo {combo_product_id}: {e}", exc_info=True)
            raise

    def replace_combo_items(self, combo_product_id: str, items: List[ComboItem]) -> None:
        try:
            for existing in self.find_combo_items(combo_product_id):
                self.session.delete(existing)
            self.session.flush()
            for item in items:
                self.session.add(item)
            self.session.flush()
        except SQLAlchemyError as e:
            logger.error(f"Error replacing combo {combo_product_id}: {e}", exc_info=True)
            raise

    # ── Modifier groups ──────────────────────────────────────────────────
    def find_groups_by_organization(self, organization_id: str) -> List[ModifierGroup]:
        try:
            stmt = (
                select(ModifierGroup)
                .options(joinedload(ModifierGroup.modifiers))
                .where(
                    and_(
                        ModifierGroup.organization_id == organization_id,
                        ModifierGroup.deleted_on.is_(None),
                    )
                )
                .order_by(ModifierGroup.sort_order, ModifierGroup.name)
            )
            return list(self.session.execute(stmt).unique().scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error loading modifier groups: {e}", exc_info=True)
            raise

    def find_group(self, group_id: uuid.UUID, organization_id: str) -> Optional[ModifierGroup]:
        try:
            stmt = (
                select(ModifierGroup)
                .options(joinedload(ModifierGroup.modifiers))
                .where(
                    and_(
                        ModifierGroup.group_id == group_id,
                        ModifierGroup.organization_id == organization_id,
                        ModifierGroup.deleted_on.is_(None),
                    )
                )
            )
            return self.session.execute(stmt).unique().scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Error loading modifier group {group_id}: {e}", exc_info=True)
            raise

    def find_groups_for_product(self, product_id: str) -> List[ModifierGroup]:
        try:
            stmt = (
                select(ModifierGroup)
                .options(joinedload(ModifierGroup.modifiers))
                .join(ProductModifierGroup, ProductModifierGroup.group_id == ModifierGroup.group_id)
                .where(
                    and_(
                        ProductModifierGroup.product_id == product_id,
                        ModifierGroup.deleted_on.is_(None),
                    )
                )
                .order_by(ProductModifierGroup.sort_order)
            )
            return list(self.session.execute(stmt).unique().scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error loading groups for product {product_id}: {e}", exc_info=True)
            raise

    def set_product_groups(self, product_id: str, group_ids: List[uuid.UUID]) -> None:
        try:
            existing = self.session.execute(
                select(ProductModifierGroup).where(
                    ProductModifierGroup.product_id == product_id
                )
            ).scalars().all()
            for row in existing:
                self.session.delete(row)
            self.session.flush()
            for idx, gid in enumerate(group_ids):
                self.session.add(
                    ProductModifierGroup(product_id=product_id, group_id=gid, sort_order=idx)
                )
            self.session.flush()
        except SQLAlchemyError as e:
            logger.error(f"Error setting groups for product {product_id}: {e}", exc_info=True)
            raise

    # ── Kitchen stations ─────────────────────────────────────────────────
    def find_stations(self, organization_id: str) -> List[KitchenStation]:
        try:
            stmt = (
                select(KitchenStation)
                .where(
                    and_(
                        KitchenStation.organization_id == organization_id,
                        KitchenStation.deleted_on.is_(None),
                    )
                )
                .order_by(KitchenStation.sort_order, KitchenStation.name)
            )
            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error loading kitchen stations: {e}", exc_info=True)
            raise

    def find_stations_for_products(self, product_ids: List[str]) -> List[ProductStation]:
        """Routing rows for a set of products — used to split a comanda."""
        if not product_ids:
            return []
        try:
            stmt = select(ProductStation).where(ProductStation.product_id.in_(product_ids))
            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error loading product stations: {e}", exc_info=True)
            raise

    def set_product_stations(self, product_id: str, station_ids: List[uuid.UUID]) -> None:
        try:
            existing = self.session.execute(
                select(ProductStation).where(ProductStation.product_id == product_id)
            ).scalars().all()
            for row in existing:
                self.session.delete(row)
            self.session.flush()
            for sid in station_ids:
                self.session.add(ProductStation(product_id=product_id, station_id=sid))
            self.session.flush()
        except SQLAlchemyError as e:
            logger.error(f"Error setting stations for product {product_id}: {e}", exc_info=True)
            raise

    def save(self, entity):
        try:
            self.session.add(entity)
            self.session.flush()
            self.session.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            logger.error(f"Error saving {type(entity).__name__}: {e}", exc_info=True)
            raise
