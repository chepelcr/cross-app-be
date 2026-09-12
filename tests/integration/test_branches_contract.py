"""Consumer half of the SAVE_BRANCHES cross-repo contract.

`SAVE_BRANCHES` is produced by `chepelcr/tsuru-sales-be` (hacienda-history) and
consumed here. Nothing type-checks that seam, and a rename on either side does
not fail a build — it fails in dev by quietly DLQ-ing branch discovery while the
sweep itself still reports success.

`tests/fixtures/save_branches_event.json` is a byte-identical copy of
sales-be's `shared/tests/fixtures/save_branches_event.json`, which that repo
asserts its producer DTO still serializes to. Here we assert the other half:
the fixture validates through our DTO and actually persists.

Two committed copies rather than one shared path, because each repo is checked
out alone in its own CI. If you change the event, regenerate both.

Runs against real PostgreSQL like the rest of this directory:
    STORE_BRANCH_SYNC_TEST_DATABASE_URL=postgresql+psycopg://... pytest tests/integration
"""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dtos.requests.branch_sync_dto import OrganizationBranchesEvent
from app.models.branch import Branch
from app.models.consecutive import Consecutive
from app.models.terminal import Terminal
from app.services.branch_sync_service import BranchSyncService

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "save_branches_event.json"

# The producer's copy, checked when both repos sit in the same tree.
PRODUCER_COPY = (
    Path(__file__).resolve().parents[3]
    / "sales-be" / "shared" / "tests" / "fixtures" / "save_branches_event.json"
)


def _event() -> OrganizationBranchesEvent:
    return OrganizationBranchesEvent.model_validate(
        json.loads(FIXTURE.read_text(encoding="utf-8"))
    )


def test_producer_event_validates_through_the_consumer_dto() -> None:
    """The strictness asymmetry is the risk: our DTO is tighter than theirs.

    The producer types `phone`/`residence` as untyped dicts and puts no upper
    bound on `currentNumber`; we validate them structurally with `strict=True`
    and `ge=1` location codes. This test is what tells us the real payload
    still clears our validators instead of retrying five times into the DLQ.
    """
    event = _event()
    assert event.event_type == "SAVE_BRANCHES"
    assert event.type_ == "OrganizationBranchesEvent"
    assert event.data.organization_id

    branch = event.data.branches[0]
    assert branch.phone is not None and branch.phone.number
    assert branch.residence is not None
    assert branch.residence.province_code and branch.residence.canton_code
    assert branch.residence.address
    assert len(branch.terminals[0].consecutives) >= 2


def test_producer_event_persists_the_orgs_own_phone_and_residence(sync_engine) -> None:
    """End to end on the real payload: branch, terminal and per-type counters."""
    event = _event()
    BranchSyncService().sync_from_hacienda(event.data.organization_id, event.data.branches)

    with Session(sync_engine) as session:
        branch = session.scalar(select(Branch))
        assert branch is not None
        assert branch.organization_id == event.data.organization_id
        assert branch.code == 1
        assert branch.created_by == "hacienda-history"
        # The organization's own contact details, as carried by the event.
        assert branch.phone == "+506 89890512"
        assert (branch.state_id, branch.county_id, branch.district_id, branch.neighborhood_id) == (6, 1, 1, 4)
        assert branch.address and branch.address.startswith("De la Escuela")

        terminal = session.scalar(select(Terminal))
        assert terminal is not None and terminal.code == 1
        assert terminal.branch_id == branch.branch_id

        counters = {
            row.document_type_id: row.current_number
            for row in session.scalars(select(Consecutive)).all()
        }
        # One counter per document type in the fixture, each at its last-used number.
        assert len(counters) == 2
        assert sorted(counters.values()) == [7, 42]


def test_both_repos_carry_the_same_fixture() -> None:
    if not PRODUCER_COPY.exists():
        import pytest

        pytest.skip(f"sales-be not checked out alongside ({PRODUCER_COPY})")

    assert json.loads(PRODUCER_COPY.read_text(encoding="utf-8")) == json.loads(
        FIXTURE.read_text(encoding="utf-8")
    ), (
        "The producer and consumer fixtures have diverged. They must stay "
        "byte-identical or the contract test proves nothing."
    )
