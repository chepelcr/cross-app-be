"""
Tests for manager-only authorization on closing approval/rejection.

**Validates: Requirement 5.7**
THE System SHALL enforce that only managers can approve or reject closings.
"""
import pytest
import uuid
from datetime import datetime, timezone
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
from app.dtos.requests.closing_request_dto import ClosingUpdateRequestDTO


@pytest.mark.integration
class TestClosingManagerAuthorization:
    """Tests for manager-only authorization on closing approval/rejection."""

    @pytest.fixture
    def test_setup(self):
        """Create test data: organization, branch, session, assignment, and closing."""
        org_id = f"test-org-{uuid.uuid4()}"
        user_id = f"test-user-{uuid.uuid4()}"
        manager_id = f"test-manager-{uuid.uuid4()}"
        
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
        
        # Create closing
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
        
        yield {
            'org_id': org_id,
            'user_id': user_id,
            'manager_id': manager_id,
            'branch': branch,
            'session': session,
            'assignment': assignment,
            'closing': closing,
        }
        
        # Cleanup
        with ClosingRepository() as repo:
            repo.delete(str(closing.closing_id))
        with AssignmentRepository() as repo:
            repo.delete(str(assignment.assignment_id))
        with SessionRepository() as repo:
            repo.delete(str(session.session_id))
        with BranchRepository() as repo:
            repo.delete(str(branch.branch_id))

    def test_manager_can_approve_closing(self, test_setup):
        """
        Test that a manager can approve a closing.
        
        **Validates: Requirement 5.7**
        """
        org_id = test_setup['org_id']
        manager_id = test_setup['manager_id']
        closing = test_setup['closing']
        
        # Manager approves closing
        dto = ClosingUpdateRequestDTO(status='approved')
        result = closing_service.update_closing(
            org_id, manager_id, str(closing.closing_id), dto, is_manager=True
        )
        
        assert result is not None
        assert result.status == 'approved'
        assert result.reviewed_by == manager_id
        assert result.reviewed_at is not None

    def test_manager_can_reject_closing(self, test_setup):
        """
        Test that a manager can reject a closing.
        
        **Validates: Requirement 5.7**
        """
        org_id = test_setup['org_id']
        manager_id = test_setup['manager_id']
        closing = test_setup['closing']
        
        # Manager rejects closing
        dto = ClosingUpdateRequestDTO(status='rejected')
        result = closing_service.update_closing(
            org_id, manager_id, str(closing.closing_id), dto, is_manager=True
        )
        
        assert result is not None
        assert result.status == 'rejected'
        assert result.reviewed_by == manager_id
        assert result.reviewed_at is not None

    def test_non_manager_cannot_approve_closing(self, test_setup):
        """
        Test that a non-manager cannot approve a closing.
        
        **Validates: Requirement 5.7**
        """
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        closing = test_setup['closing']
        
        # Non-manager attempts to approve closing
        dto = ClosingUpdateRequestDTO(status='approved')
        
        with pytest.raises(PermissionError) as exc_info:
            closing_service.update_closing(
                org_id, user_id, str(closing.closing_id), dto, is_manager=False
            )
        
        assert "Only managers can approve or reject closings" in str(exc_info.value)
        
        # Verify closing status unchanged
        result = closing_service.get_closing(org_id, user_id, str(closing.closing_id))
        assert result.status == 'pending'

    def test_non_manager_cannot_reject_closing(self, test_setup):
        """
        Test that a non-manager cannot reject a closing.
        
        **Validates: Requirement 5.7**
        """
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        closing = test_setup['closing']
        
        # Non-manager attempts to reject closing
        dto = ClosingUpdateRequestDTO(status='rejected')
        
        with pytest.raises(PermissionError) as exc_info:
            closing_service.update_closing(
                org_id, user_id, str(closing.closing_id), dto, is_manager=False
            )
        
        assert "Only managers can approve or reject closings" in str(exc_info.value)
        
        # Verify closing status unchanged
        result = closing_service.get_closing(org_id, user_id, str(closing.closing_id))
        assert result.status == 'pending'

    def test_non_manager_can_update_notes(self, test_setup):
        """
        Test that a non-manager can update notes (non-status fields).
        
        **Validates: Requirement 5.7** (only approval/rejection restricted)
        """
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        closing = test_setup['closing']
        
        # Non-manager updates notes (allowed)
        dto = ClosingUpdateRequestDTO(notes="Updated notes from cashier")
        result = closing_service.update_closing(
            org_id, user_id, str(closing.closing_id), dto, is_manager=False
        )
        
        assert result is not None
        assert result.notes == "Updated notes from cashier"
        assert result.status == 'pending'  # Status unchanged

    def test_non_manager_can_set_status_to_pending(self, test_setup):
        """
        Test that a non-manager can set status to 'pending'.
        
        **Validates: Requirement 5.7** (only approval/rejection restricted)
        """
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        closing = test_setup['closing']
        
        # Non-manager sets status to pending (allowed)
        dto = ClosingUpdateRequestDTO(status='pending')
        result = closing_service.update_closing(
            org_id, user_id, str(closing.closing_id), dto, is_manager=False
        )
        
        assert result is not None
        assert result.status == 'pending'

    def test_manager_can_update_notes_and_approve(self, test_setup):
        """
        Test that a manager can update both notes and status in one operation.
        
        **Validates: Requirement 5.7**
        """
        org_id = test_setup['org_id']
        manager_id = test_setup['manager_id']
        closing = test_setup['closing']
        
        # Manager approves with notes
        dto = ClosingUpdateRequestDTO(
            status='approved',
            notes="Approved by manager - all amounts correct"
        )
        result = closing_service.update_closing(
            org_id, manager_id, str(closing.closing_id), dto, is_manager=True
        )
        
        assert result is not None
        assert result.status == 'approved'
        assert result.notes == "Approved by manager - all amounts correct"
        assert result.reviewed_by == manager_id
        assert result.reviewed_at is not None

    def test_authorization_check_only_for_approval_rejection(self, test_setup):
        """
        Test that authorization is only checked for 'approved' and 'rejected' statuses.
        
        **Validates: Requirement 5.7** (specific to approval/rejection)
        """
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        closing = test_setup['closing']
        
        # Non-manager can update to pending (no authorization check)
        dto = ClosingUpdateRequestDTO(status='pending', notes="Back to pending")
        result = closing_service.update_closing(
            org_id, user_id, str(closing.closing_id), dto, is_manager=False
        )
        assert result is not None
        assert result.status == 'pending'
        
        # Non-manager cannot update to approved (authorization check)
        dto = ClosingUpdateRequestDTO(status='approved')
        with pytest.raises(PermissionError):
            closing_service.update_closing(
                org_id, user_id, str(closing.closing_id), dto, is_manager=False
            )
        
        # Non-manager cannot update to rejected (authorization check)
        dto = ClosingUpdateRequestDTO(status='rejected')
        with pytest.raises(PermissionError):
            closing_service.update_closing(
                org_id, user_id, str(closing.closing_id), dto, is_manager=False
            )

    def test_manager_approval_sets_reviewed_fields(self, test_setup):
        """
        Test that manager approval automatically sets reviewed_by and reviewed_at.
        
        **Validates: Requirements 5.5, 5.6**
        """
        org_id = test_setup['org_id']
        manager_id = test_setup['manager_id']
        closing = test_setup['closing']
        
        # Verify initial state
        result = closing_service.get_closing(org_id, manager_id, str(closing.closing_id))
        assert result.reviewed_by is None
        assert result.reviewed_at is None
        
        # Manager approves
        dto = ClosingUpdateRequestDTO(status='approved')
        result = closing_service.update_closing(
            org_id, manager_id, str(closing.closing_id), dto, is_manager=True
        )
        
        # Verify reviewed fields are set
        assert result.reviewed_by == manager_id
        assert result.reviewed_at is not None
        assert isinstance(result.reviewed_at, str)  # ISO format

    def test_manager_rejection_sets_reviewed_fields(self, test_setup):
        """
        Test that manager rejection automatically sets reviewed_by and reviewed_at.
        
        **Validates: Requirements 5.5, 5.6**
        """
        org_id = test_setup['org_id']
        manager_id = test_setup['manager_id']
        closing = test_setup['closing']
        
        # Verify initial state
        result = closing_service.get_closing(org_id, manager_id, str(closing.closing_id))
        assert result.reviewed_by is None
        assert result.reviewed_at is None
        
        # Manager rejects
        dto = ClosingUpdateRequestDTO(status='rejected')
        result = closing_service.update_closing(
            org_id, manager_id, str(closing.closing_id), dto, is_manager=True
        )
        
        # Verify reviewed fields are set
        assert result.reviewed_by == manager_id
        assert result.reviewed_at is not None
        assert isinstance(result.reviewed_at, str)  # ISO format

    def test_explicit_reviewed_by_overrides_user_id(self, test_setup):
        """
        Test that explicit reviewed_by in DTO overrides the user_id parameter.
        
        **Validates: Requirement 5.5**
        """
        org_id = test_setup['org_id']
        manager_id = test_setup['manager_id']
        other_manager_id = f"other-manager-{uuid.uuid4()}"
        closing = test_setup['closing']
        
        # Manager approves but specifies different reviewer
        dto = ClosingUpdateRequestDTO(
            status='approved',
            reviewed_by=other_manager_id
        )
        result = closing_service.update_closing(
            org_id, manager_id, str(closing.closing_id), dto, is_manager=True
        )
        
        # Verify reviewed_by uses the explicit value
        assert result.reviewed_by == other_manager_id
        assert result.reviewed_at is not None
