"""Shared PostgreSQL fixture for the branch-discovery integration probes.

Lives in a conftest rather than one test module because two files need it:
`test_branch_sync.py` (idempotency + concurrency) and `test_branches_contract.py`
(the cross-repo SAVE_BRANCHES contract).

Set STORE_BRANCH_SYNC_TEST_DATABASE_URL to an isolated PostgreSQL database. Each
test creates and drops only its own randomly named schema, so no cloud DB is
needed and runs cannot collide.
"""

import os
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.configuration.database_connection import DatabaseConnection
from app.models.base import Base
from app.models.branch import Branch
from app.models.branch_type import BranchType
from app.models.consecutive import Consecutive
from app.models.document_type import DocumentType
from app.models.terminal import Terminal


@pytest.fixture
def sync_engine(monkeypatch):
    url = os.environ.get("STORE_BRANCH_SYNC_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set STORE_BRANCH_SYNC_TEST_DATABASE_URL for PostgreSQL probes")
    admin_engine = create_engine(url)
    schema = f"branch_sync_test_{uuid.uuid4().hex}"
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    try:
        Base.metadata.create_all(engine, tables=[
            Branch.__table__, BranchType.__table__, Terminal.__table__,
            DocumentType.__table__, Consecutive.__table__,
        ])
        with Session(engine) as session, session.begin():
            # The catalog id intentionally differs from the fiscal code.
            session.add(DocumentType(id=101, code="01", description="Factura", country_code="188", status=1))
            session.add(DocumentType(id=103, code="03", description="Nota", country_code="188", status=1))
            # Tiquete electrónico — the second type in the SAVE_BRANCHES
            # contract fixture, so a per-type counter bug cannot hide behind
            # a single document type.
            session.add(DocumentType(id=104, code="04", description="Tiquete", country_code="188", status=1))
        monkeypatch.setattr(DatabaseConnection, "_engine", engine)
        monkeypatch.setattr(DatabaseConnection, "_session_factory", sessionmaker(bind=engine, expire_on_commit=False))
        yield engine
    finally:
        engine.dispose()
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin_engine.dispose()
