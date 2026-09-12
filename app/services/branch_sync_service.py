"""Persist Hacienda branch discovery without replacing operator configuration."""

from __future__ import annotations

from app.configuration.database_connection import DatabaseConnection
from app.dtos.requests.branch_sync_dto import BranchSyncDTO
from app.repositories.branch_repository import BranchRepository
from app.repositories.branch_type_repository import BranchTypeRepository
from app.repositories.consecutive_repository import ConsecutiveRepository
from app.repositories.document_type_repository import DocumentTypeRepository
from app.repositories.terminal_repository import TerminalRepository


class BranchSyncService:
    def sync_from_hacienda(self, organization_id: str, branches: list) -> None:
        """Apply one message in one transaction; duplicate/reordered events are safe."""
        if not organization_id or not organization_id.strip():
            raise ValueError("organization_id is required")
        payload = [
            item if isinstance(item, BranchSyncDTO) else BranchSyncDTO.model_validate(item)
            for item in branches
        ]
        with DatabaseConnection() as db:
            branch_repo = BranchRepository.from_session(db.session)
            terminal_repo = TerminalRepository.from_session(db.session)
            consecutive_repo = ConsecutiveRepository.from_session(db.session)
            type_repo = BranchTypeRepository.from_session(db.session)
            document_repo = DocumentTypeRepository.from_session(db.session)
            branch_types = type_repo.find_all_by_organization(organization_id)
            default_type = branch_types[0].code if branch_types else "stand"
            document_types = {}

            # Stable lock order also avoids deadlocks if publishers reorder rows.
            for incoming in sorted(payload, key=lambda branch: branch.number):
                residence = incoming.residence
                phone = incoming.phone
                phone_number = None
                if phone and phone.number is not None:
                    phone_number = str(phone.number)
                    if phone.country_code is not None:
                        phone_number = f"+{phone.country_code} {phone_number}"
                branch = branch_repo.insert_from_history(
                    organization_id=organization_id,
                    code=incoming.number,
                    name=incoming.name or f"Sucursal {incoming.number:03d}",
                    type=default_type,
                    created_by="hacienda-history",
                    state_id=residence.province_code if residence else None,
                    county_id=residence.canton_code if residence else None,
                    district_id=residence.district_code if residence else None,
                    neighborhood_id=residence.neighborhood_code if residence else None,
                    address=residence.address if residence else None,
                    phone=phone_number,
                )
                for incoming_terminal in sorted(incoming.terminals, key=lambda terminal: terminal.number):
                    terminal = terminal_repo.insert_from_history(
                        organization_id=organization_id,
                        branch_id=branch.branch_id,
                        code=incoming_terminal.number,
                        name=incoming_terminal.name or f"Terminal {incoming_terminal.number}",
                    )
                    for counter in sorted(incoming_terminal.consecutives, key=lambda item: item.document_type):
                        if counter.document_type not in document_types:
                            doc_type = document_repo.find_by_code(counter.document_type)
                            if doc_type is None:
                                raise ValueError(f"Unknown document type {counter.document_type}")
                            document_types[counter.document_type] = doc_type.id
                        consecutive_repo.raise_from_history(
                            organization_id,
                            str(terminal.terminal_id),
                            document_types[counter.document_type],
                            counter.current_number,
                        )

            # The legacy context manager logs and swallows commit failures. Commit
            # here so a failed write reaches Powertools and the message is retried.
            db.session.commit()
