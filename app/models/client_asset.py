from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base


class ClientAsset(Base, AuditMixin):
    """A thing a taller works ON: a vehicle, a machine, a piece of equipment.

    Scoped to the CLIENT, exactly like `departments` and `stores`, because that
    is what makes it worth a table rather than a blob on the order: the value of
    the workshop vertical is largely "what did we do to this car last time", and
    that only exists if the asset outlives the visit.

    Per-visit facts (odometer, reported fault) stay on the order — they describe
    the visit, not the asset.
    """

    __tablename__ = "client_assets"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[str] = mapped_column(String(50), nullable=False)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.client_id"), nullable=False
    )

    #: Placa, serie or whatever the shop uses to tell one asset from another.
    identifier: Mapped[str] = mapped_column(String(50), nullable=False)
    #: Free vocabulary ("vehiculo", "moto", "equipo") — deliberately not an enum:
    #: a taller de refrigeración and a taller mecánico do not share a list.
    kind: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    client: Mapped["Client"] = relationship(back_populates="assets")

    __table_args__ = (
        Index("idx_client_asset_org", "organization_id"),
        Index("idx_client_asset_client", "client_id"),
        # One placa per client: the same plate twice is a data-entry mistake,
        # and the history view depends on it being one row.
        Index(
            "idx_client_asset_client_identifier",
            "client_id",
            "identifier",
            unique=True,
        ),
    )
