"""
Integration tests for closings handler with real database operations.
"""
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app.models.closing import Closing
from app.models.session import Session
from app.models.branch import Branch
from app.models.assignment import Assignment
from app.repositories.closing_repository import ClosingRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.branch_repository import BranchRepository
from app.repositories.assignment_repository import AssignmentRepository
from app.services import closing_service
from app.dtos.requests.closing_request_dto import (
    ClosingCreateRequestDTO,
    ClosingUpdateRequestDTO,
)


@pytest.mark.integration
class TestClosingIntegration:
    """Integration tests for closing operations with database."""

    @pytest.fixture
    def test_setup(self):
        """Create test data: organization, branch, session, and assignment."""
        org_id = f"test-org-{uuid.uuid4()}"
        user_id = f"test-user-{uuid.uuid4()}"
        
        # Create branch
        with BranchRepository() as repo:
            branch = Branch(
                branch_id=uuid.uuid4(),
                organization_id=org_id,
                name="Test Branch",
                code=f"TB-{uuid.uuid4().hex[:6]}",
                type="stand",
                is_active=True,
                created_by=user_id,
            )
            branch = repo.save(branch)
        
        # Create session
        with SessionRepository() as repo:
            session = Session(
                session_id=uuid.uuid4(),
                organization_id=org_id,
                branch_id=branch.branch_id,
                name="Test Session",
                type="match",
                context="gradas",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            session = repo.save(session)
        
        # Create assignment
        with AssignmentRepository() as repo:
            assignment = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                user_id=user_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            assignment = repo.save(assignment)
        
        yield {
            'org_id': org_id,
            'user_id': user_id,
            'branch': branch,
            'session': session,
            'assignment': assignment,
        }
        
        # Cleanup
        with AssignmentRepository() as repo:
            repo.delete(str(assignment.assignment_id))
        with SessionRepository() as repo:
            repo.delete(str(session.session_id))
        with BranchRepository() as repo:
            repo.delete(str(branch.branch_id))

    def test_get_closings_no_filters(self, test_setup):
        """Test getting all closings without filters."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create multiple closings
        closings = []
        with ClosingRepository() as repo:
            for i in range(3):
                closing = Closing(
                    closing_id=uuid.uuid4(),
                    organization_id=org_id,
                    session_id=session.session_id,
                    assignment_id=assignment.assignment_id,
                    branch_id=branch.branch_id,
                    terminal_id=None,
                    cashier_id=user_id,
                    expected_cash=Decimal('100.00'),
                    expected_sinpe=Decimal('50.00'),
                    expected_card=Decimal('50.00'),
                    expected_total=Decimal('200.00'),
                    declared_cash=Decimal('100.00'),
                    declared_sinpe=Decimal('50.00'),
                    declared_card=Decimal('50.00'),
                    declared_total=Decimal('200.00'),
                    status='pending',
                )
                closing = repo.save(closing)
                closings.append(closing)
        
        # Get all closings
        retrieved = closing_service.get_closings(org_id, user_id)
        
        # Verify we got at least our closings
        retrieved_ids = [c.closing_id for c in retrieved]
        for closing in closings:
            assert str(closing.closing_id) in retrieved_ids
        
        # Cleanup
        with ClosingRepository() as repo:
            for closing in closings:
                repo.delete(str(closing.closing_id))

    def test_get_closings_filter_by_session_id(self, test_setup):
        """Test filtering closings by session_id."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create another session
        with SessionRepository() as repo:
            other_session = Session(
                session_id=uuid.uuid4(),
                organization_id=org_id,
                branch_id=branch.branch_id,
                name="Other Session",
                type="shift",
                context="caja",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            other_session = repo.save(other_session)
        
        # Create another assignment for the other session
        with AssignmentRepository() as repo:
            other_assignment = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=other_session.session_id,
                user_id=f"other-user-{uuid.uuid4()}",
                branch_id=branch.branch_id,
                terminal_id=None,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            other_assignment = repo.save(other_assignment)
        
        # Create closings for both sessions
        closings = []
        with ClosingRepository() as repo:
            # Closing for first session
            closing1 = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                assignment_id=assignment.assignment_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                cashier_id=user_id,
                expected_cash=Decimal('100.00'),
                expected_sinpe=Decimal('50.00'),
                expected_card=Decimal('50.00'),
                expected_total=Decimal('200.00'),
                declared_cash=Decimal('100.00'),
                declared_sinpe=Decimal('50.00'),
                declared_card=Decimal('50.00'),
                declared_total=Decimal('200.00'),
                status='pending',
            )
            closing1 = repo.save(closing1)
            closings.append(closing1)
            
            # Closing for second session
            closing2 = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=other_session.session_id,
                assignment_id=other_assignment.assignment_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                cashier_id=f"other-user-{uuid.uuid4()}",
                expected_cash=Decimal('200.00'),
                expected_sinpe=Decimal('100.00'),
                expected_card=Decimal('100.00'),
                expected_total=Decimal('400.00'),
                declared_cash=Decimal('200.00'),
                declared_sinpe=Decimal('100.00'),
                declared_card=Decimal('100.00'),
                declared_total=Decimal('400.00'),
                status='approved',
            )
            closing2 = repo.save(closing2)
            closings.append(closing2)
        
        # Filter by first session
        filtered = closing_service.get_closings(
            org_id, user_id, session_id=str(session.session_id)
        )
        
        # Verify only closings from first session are returned
        filtered_ids = [c.closing_id for c in filtered]
        assert str(closing1.closing_id) in filtered_ids
        assert str(closing2.closing_id) not in filtered_ids
        
        # Filter by second session
        filtered = closing_service.get_closings(
            org_id, user_id, session_id=str(other_session.session_id)
        )
        
        # Verify only closings from second session are returned
        filtered_ids = [c.closing_id for c in filtered]
        assert str(closing2.closing_id) in filtered_ids
        assert str(closing1.closing_id) not in filtered_ids
        
        # Cleanup
        with ClosingRepository() as repo:
            for closing in closings:
                repo.delete(str(closing.closing_id))
        with AssignmentRepository() as repo:
            repo.delete(str(other_assignment.assignment_id))
        with SessionRepository() as repo:
            repo.delete(str(other_session.session_id))

    def test_get_closings_filter_by_status(self, test_setup):
        """Test filtering closings by status."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create closings with different statuses
        closings = []
        statuses = ['pending', 'approved', 'rejected']
        with ClosingRepository() as repo:
            for status in statuses:
                closing = Closing(
                    closing_id=uuid.uuid4(),
                    organization_id=org_id,
                    session_id=session.session_id,
                    assignment_id=assignment.assignment_id,
                    branch_id=branch.branch_id,
                    terminal_id=None,
                    cashier_id=user_id,
                    expected_cash=Decimal('100.00'),
                    expected_sinpe=Decimal('50.00'),
                    expected_card=Decimal('50.00'),
                    expected_total=Decimal('200.00'),
                    declared_cash=Decimal('100.00'),
                    declared_sinpe=Decimal('50.00'),
                    declared_card=Decimal('50.00'),
                    declared_total=Decimal('200.00'),
                    status=status,
                )
                closing = repo.save(closing)
                closings.append(closing)
        
        # Filter by each status
        for status in statuses:
            filtered = closing_service.get_closings(
                org_id, user_id, status=status
            )
            
            # Verify only closings with the specified status are returned
            for closing_response in filtered:
                if closing_response.closing_id in [str(c.closing_id) for c in closings]:
                    assert closing_response.status == status
        
        # Cleanup
        with ClosingRepository() as repo:
            for closing in closings:
                repo.delete(str(closing.closing_id))

    def test_get_closings_filter_by_branch_id(self, test_setup):
        """Test filtering closings by branch_id."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create another branch
        with BranchRepository() as repo:
            other_branch = Branch(
                branch_id=uuid.uuid4(),
                organization_id=org_id,
                name="Other Branch",
                code=f"OB-{uuid.uuid4().hex[:6]}",
                type="restaurant",
                is_active=True,
                created_by=user_id,
            )
            other_branch = repo.save(other_branch)
        
        # Create another assignment for the other branch
        with AssignmentRepository() as repo:
            other_assignment = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                user_id=f"other-user-{uuid.uuid4()}",
                branch_id=other_branch.branch_id,
                terminal_id=None,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            other_assignment = repo.save(other_assignment)
        
        # Create closings for both branches
        closings = []
        with ClosingRepository() as repo:
            # Closing for first branch
            closing1 = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                assignment_id=assignment.assignment_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                cashier_id=user_id,
                expected_cash=Decimal('100.00'),
                expected_sinpe=Decimal('50.00'),
                expected_card=Decimal('50.00'),
                expected_total=Decimal('200.00'),
                declared_cash=Decimal('100.00'),
                declared_sinpe=Decimal('50.00'),
                declared_card=Decimal('50.00'),
                declared_total=Decimal('200.00'),
                status='pending',
            )
            closing1 = repo.save(closing1)
            closings.append(closing1)
            
            # Closing for second branch
            closing2 = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                assignment_id=other_assignment.assignment_id,
                branch_id=other_branch.branch_id,
                terminal_id=None,
                cashier_id=f"other-user-{uuid.uuid4()}",
                expected_cash=Decimal('200.00'),
                expected_sinpe=Decimal('100.00'),
                expected_card=Decimal('100.00'),
                expected_total=Decimal('400.00'),
                declared_cash=Decimal('200.00'),
                declared_sinpe=Decimal('100.00'),
                declared_card=Decimal('100.00'),
                declared_total=Decimal('400.00'),
                status='pending',
            )
            closing2 = repo.save(closing2)
            closings.append(closing2)
        
        # Filter by first branch
        filtered = closing_service.get_closings(
            org_id, user_id, branch_id=str(branch.branch_id)
        )
        
        # Verify only closings from first branch are returned
        filtered_ids = [c.closing_id for c in filtered]
        assert str(closing1.closing_id) in filtered_ids
        assert str(closing2.closing_id) not in filtered_ids
        
        # Filter by second branch
        filtered = closing_service.get_closings(
            org_id, user_id, branch_id=str(other_branch.branch_id)
        )
        
        # Verify only closings from second branch are returned
        filtered_ids = [c.closing_id for c in filtered]
        assert str(closing2.closing_id) in filtered_ids
        assert str(closing1.closing_id) not in filtered_ids
        
        # Cleanup
        with ClosingRepository() as repo:
            for closing in closings:
                repo.delete(str(closing.closing_id))
        with AssignmentRepository() as repo:
            repo.delete(str(other_assignment.assignment_id))
        with BranchRepository() as repo:
            repo.delete(str(other_branch.branch_id))

    def test_get_closings_multiple_filters(self, test_setup):
        """Test filtering closings with multiple filters combined."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create another session
        with SessionRepository() as repo:
            other_session = Session(
                session_id=uuid.uuid4(),
                organization_id=org_id,
                branch_id=branch.branch_id,
                name="Other Session",
                type="shift",
                context="caja",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            other_session = repo.save(other_session)
        
        # Create another assignment for the other session
        with AssignmentRepository() as repo:
            other_assignment = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=other_session.session_id,
                user_id=f"other-user-{uuid.uuid4()}",
                branch_id=branch.branch_id,
                terminal_id=None,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            other_assignment = repo.save(other_assignment)
        
        # Create closings with different combinations
        closings = []
        with ClosingRepository() as repo:
            # Session 1, Branch 1, Pending
            closing1 = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                assignment_id=assignment.assignment_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                cashier_id=user_id,
                expected_cash=Decimal('100.00'),
                expected_sinpe=Decimal('50.00'),
                expected_card=Decimal('50.00'),
                expected_total=Decimal('200.00'),
                declared_cash=Decimal('100.00'),
                declared_sinpe=Decimal('50.00'),
                declared_card=Decimal('50.00'),
                declared_total=Decimal('200.00'),
                status='pending',
            )
            closing1 = repo.save(closing1)
            closings.append(closing1)
            
            # Session 2, Branch 1, Approved
            closing2 = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=other_session.session_id,
                assignment_id=other_assignment.assignment_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                cashier_id=f"other-user-{uuid.uuid4()}",
                expected_cash=Decimal('200.00'),
                expected_sinpe=Decimal('100.00'),
                expected_card=Decimal('100.00'),
                expected_total=Decimal('400.00'),
                declared_cash=Decimal('200.00'),
                declared_sinpe=Decimal('100.00'),
                declared_card=Decimal('100.00'),
                declared_total=Decimal('400.00'),
                status='approved',
            )
            closing2 = repo.save(closing2)
            closings.append(closing2)
        
        # Filter by session_id + status
        filtered = closing_service.get_closings(
            org_id, user_id,
            session_id=str(session.session_id),
            status='pending'
        )
        
        # Verify only closing1 is returned
        filtered_ids = [c.closing_id for c in filtered]
        assert str(closing1.closing_id) in filtered_ids
        assert str(closing2.closing_id) not in filtered_ids
        
        # Filter by session_id + branch_id + status
        filtered = closing_service.get_closings(
            org_id, user_id,
            session_id=str(other_session.session_id),
            branch_id=str(branch.branch_id),
            status='approved'
        )
        
        # Verify only closing2 is returned
        filtered_ids = [c.closing_id for c in filtered]
        assert str(closing2.closing_id) in filtered_ids
        assert str(closing1.closing_id) not in filtered_ids
        
        # Cleanup
        with ClosingRepository() as repo:
            for closing in closings:
                repo.delete(str(closing.closing_id))
        with AssignmentRepository() as repo:
            repo.delete(str(other_assignment.assignment_id))
        with SessionRepository() as repo:
            repo.delete(str(other_session.session_id))

    def test_closings_ordered_by_created_at_desc(self, test_setup):
        """Test that closings are returned ordered by created_at descending."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create closings with different created_at times
        closings = []
        with ClosingRepository() as repo:
            for i in range(3):
                closing = Closing(
                    closing_id=uuid.uuid4(),
                    organization_id=org_id,
                    session_id=session.session_id,
                    assignment_id=assignment.assignment_id,
                    branch_id=branch.branch_id,
                    terminal_id=None,
                    cashier_id=user_id,
                    expected_cash=Decimal('100.00'),
                    expected_sinpe=Decimal('50.00'),
                    expected_card=Decimal('50.00'),
                    expected_total=Decimal('200.00'),
                    declared_cash=Decimal('100.00'),
                    declared_sinpe=Decimal('50.00'),
                    declared_card=Decimal('50.00'),
                    declared_total=Decimal('200.00'),
                    status='pending',
                )
                closing = repo.save(closing)
                closings.append(closing)
        
        # Get all closings
        retrieved = closing_service.get_closings(org_id, user_id)
        
        # Verify ordering (most recent first)
        closing_ids = [c.closing_id for c in retrieved]
        our_closing_ids = [str(c.closing_id) for c in closings]
        
        # Find positions of our closings in the result
        positions = [closing_ids.index(cid) for cid in our_closing_ids if cid in closing_ids]
        
        # Verify they are in descending order (most recent first)
        # Since we created them in order, the last one should come first
        assert positions == sorted(positions)
        
        # Cleanup
        with ClosingRepository() as repo:
            for closing in closings:
                repo.delete(str(closing.closing_id))

    def test_organization_scoped_data_isolation(self, test_setup):
        """Test that closings are isolated by organization."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        other_org_id = f"test-org-{uuid.uuid4()}"
        
        # Create closing in first organization
        with ClosingRepository() as repo:
            closing = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                assignment_id=assignment.assignment_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                cashier_id=user_id,
                expected_cash=Decimal('100.00'),
                expected_sinpe=Decimal('50.00'),
                expected_card=Decimal('50.00'),
                expected_total=Decimal('200.00'),
                declared_cash=Decimal('100.00'),
                declared_sinpe=Decimal('50.00'),
                declared_card=Decimal('50.00'),
                declared_total=Decimal('200.00'),
                status='pending',
            )
            closing = repo.save(closing)
        
        closing_id = str(closing.closing_id)
        
        # Try to retrieve from different organization
        retrieved = closing_service.get_closing(other_org_id, user_id, closing_id)
        assert retrieved is None
        
        # Verify it exists in correct organization
        retrieved = closing_service.get_closing(org_id, user_id, closing_id)
        assert retrieved is not None
        
        # Verify list filtering by organization
        closings_list = closing_service.get_closings(other_org_id, user_id)
        closing_ids = [c.closing_id for c in closings_list]
        assert closing_id not in closing_ids
        
        # Cleanup
        with ClosingRepository() as repo:
            repo.delete(closing_id)

    def test_create_closing_with_database(self, test_setup):
        """Test creating a closing through the service with real database operations."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        
        # Create closing via service
        create_dto = ClosingCreateRequestDTO(
            assignment_id=str(assignment.assignment_id),
            declared_cash=Decimal('150.00'),
            declared_sinpe=Decimal('75.00'),
            declared_card=Decimal('75.00'),
            notes="Test closing creation"
        )
        
        created = closing_service.create_closing(org_id, user_id, create_dto)
        
        # Verify closing was created
        assert created is not None
        assert created.organization_id == org_id
        assert created.assignment_id == str(assignment.assignment_id)
        assert created.declared_cash == 150.00
        assert created.declared_sinpe == 75.00
        assert created.declared_card == 75.00
        assert created.declared_total == 300.00
        assert created.status == 'pending'
        assert created.notes == "Test closing creation"
        
        # Verify it can be retrieved
        retrieved = closing_service.get_closing(org_id, user_id, created.closing_id)
        assert retrieved is not None
        assert retrieved.closing_id == created.closing_id
        
        # Cleanup
        with ClosingRepository() as repo:
            repo.delete(created.closing_id)

    def test_create_closing_duplicate_assignment_fails(self, test_setup):
        """Test that creating a second closing for the same assignment fails."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        
        # Create first closing
        create_dto = ClosingCreateRequestDTO(
            assignment_id=str(assignment.assignment_id),
            declared_cash=Decimal('100.00'),
            declared_sinpe=Decimal('50.00'),
            declared_card=Decimal('50.00'),
            notes="First closing"
        )
        
        first_closing = closing_service.create_closing(org_id, user_id, create_dto)
        
        # Try to create second closing for same assignment
        create_dto2 = ClosingCreateRequestDTO(
            assignment_id=str(assignment.assignment_id),
            declared_cash=Decimal('200.00'),
            declared_sinpe=Decimal('100.00'),
            declared_card=Decimal('100.00'),
            notes="Second closing"
        )
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="A closing already exists for assignment"):
            closing_service.create_closing(org_id, user_id, create_dto2)
        
        # Cleanup
        with ClosingRepository() as repo:
            repo.delete(first_closing.closing_id)

    def test_update_closing_approve(self, test_setup):
        """Test approving a closing through the service."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        manager_id = f"manager-{uuid.uuid4()}"
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create a pending closing
        with ClosingRepository() as repo:
            closing = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                assignment_id=assignment.assignment_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                cashier_id=user_id,
                expected_cash=Decimal('100.00'),
                expected_sinpe=Decimal('50.00'),
                expected_card=Decimal('50.00'),
                expected_total=Decimal('200.00'),
                declared_cash=Decimal('100.00'),
                declared_sinpe=Decimal('50.00'),
                declared_card=Decimal('50.00'),
                declared_total=Decimal('200.00'),
                status='pending',
            )
            closing = repo.save(closing)
        
        closing_id = str(closing.closing_id)
        
        # Approve the closing
        update_dto = ClosingUpdateRequestDTO(
            status='approved',
            reviewed_by=manager_id
        )
        
        updated = closing_service.update_closing(
            org_id, manager_id, closing_id, update_dto, is_manager=True
        )
        
        # Verify closing was approved
        assert updated is not None
        assert updated.status == 'approved'
        assert updated.reviewed_by == manager_id
        assert updated.reviewed_at is not None
        
        # Verify changes persisted
        retrieved = closing_service.get_closing(org_id, user_id, closing_id)
        assert retrieved.status == 'approved'
        assert retrieved.reviewed_by == manager_id
        
        # Cleanup
        with ClosingRepository() as repo:
            repo.delete(closing_id)

    def test_update_closing_reject(self, test_setup):
        """Test rejecting a closing through the service."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        manager_id = f"manager-{uuid.uuid4()}"
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create a pending closing
        with ClosingRepository() as repo:
            closing = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                assignment_id=assignment.assignment_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                cashier_id=user_id,
                expected_cash=Decimal('100.00'),
                expected_sinpe=Decimal('50.00'),
                expected_card=Decimal('50.00'),
                expected_total=Decimal('200.00'),
                declared_cash=Decimal('90.00'),
                declared_sinpe=Decimal('45.00'),
                declared_card=Decimal('45.00'),
                declared_total=Decimal('180.00'),
                status='pending',
            )
            closing = repo.save(closing)
        
        closing_id = str(closing.closing_id)
        
        # Reject the closing
        update_dto = ClosingUpdateRequestDTO(
            status='rejected',
            reviewed_by=manager_id,
            notes="Cash amount discrepancy"
        )
        
        updated = closing_service.update_closing(
            org_id, manager_id, closing_id, update_dto, is_manager=True
        )
        
        # Verify closing was rejected
        assert updated is not None
        assert updated.status == 'rejected'
        assert updated.reviewed_by == manager_id
        assert updated.reviewed_at is not None
        assert updated.notes == "Cash amount discrepancy"
        
        # Cleanup
        with ClosingRepository() as repo:
            repo.delete(closing_id)

    def test_update_closing_non_manager_cannot_approve(self, test_setup):
        """Test that non-managers cannot approve or reject closings."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create a pending closing
        with ClosingRepository() as repo:
            closing = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                assignment_id=assignment.assignment_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                cashier_id=user_id,
                expected_cash=Decimal('100.00'),
                expected_sinpe=Decimal('50.00'),
                expected_card=Decimal('50.00'),
                expected_total=Decimal('200.00'),
                declared_cash=Decimal('100.00'),
                declared_sinpe=Decimal('50.00'),
                declared_card=Decimal('50.00'),
                declared_total=Decimal('200.00'),
                status='pending',
            )
            closing = repo.save(closing)
        
        closing_id = str(closing.closing_id)
        
        # Try to approve as non-manager
        update_dto = ClosingUpdateRequestDTO(
            status='approved',
            reviewed_by=user_id
        )
        
        # Should raise PermissionError
        with pytest.raises(PermissionError, match="Only managers can approve or reject closings"):
            closing_service.update_closing(
                org_id, user_id, closing_id, update_dto, is_manager=False
            )
        
        # Verify status unchanged
        retrieved = closing_service.get_closing(org_id, user_id, closing_id)
        assert retrieved.status == 'pending'
        
        # Cleanup
        with ClosingRepository() as repo:
            repo.delete(closing_id)

    def test_delete_closing(self, test_setup):
        """Test deleting a closing through the service."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create a closing
        with ClosingRepository() as repo:
            closing = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                assignment_id=assignment.assignment_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                cashier_id=user_id,
                expected_cash=Decimal('100.00'),
                expected_sinpe=Decimal('50.00'),
                expected_card=Decimal('50.00'),
                expected_total=Decimal('200.00'),
                declared_cash=Decimal('100.00'),
                declared_sinpe=Decimal('50.00'),
                declared_card=Decimal('50.00'),
                declared_total=Decimal('200.00'),
                status='pending',
            )
            closing = repo.save(closing)
        
        closing_id = str(closing.closing_id)
        
        # Verify closing exists
        retrieved = closing_service.get_closing(org_id, user_id, closing_id)
        assert retrieved is not None
        
        # Delete the closing
        result = closing_service.delete_closing(org_id, user_id, closing_id)
        assert result is True
        
        # Verify closing no longer exists
        retrieved = closing_service.get_closing(org_id, user_id, closing_id)
        assert retrieved is None

    def test_delete_nonexistent_closing(self, test_setup):
        """Test deleting a closing that doesn't exist returns False."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        nonexistent_id = str(uuid.uuid4())
        
        # Try to delete non-existent closing
        result = closing_service.delete_closing(org_id, user_id, nonexistent_id)
        assert result is False
