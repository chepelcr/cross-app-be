"""
Unit tests for manager-only authorization on closing approval/rejection.
These tests verify the authorization logic without requiring database access.

**Validates: Requirement 5.7**
THE System SHALL enforce that only managers can approve or reject closings.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timezone
import uuid

from app.services import closing_service
from app.dtos.requests.closing_request_dto import ClosingUpdateRequestDTO
from app.models.closing import Closing


class TestClosingAuthorizationUnit:
    """Unit tests for closing authorization logic."""

    @patch('app.services.closing_service.ClosingRepository')
    def test_manager_can_approve_closing(self, mock_repo_class):
        """
        Test that a manager can approve a closing.
        
        **Validates: Requirement 5.7**
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        closing = Closing(
            closing_id=uuid.uuid4(),
            organization_id="org-123",
            session_id=uuid.uuid4(),
            assignment_id=uuid.uuid4(),
            branch_id=uuid.uuid4(),
            terminal_id=None,
            cashier_id="cashier-123",
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
        
        mock_repo.find_by_id_and_organization.return_value = closing
        mock_repo.save.return_value = closing
        
        # Manager approves closing
        dto = ClosingUpdateRequestDTO(status='approved')
        result = closing_service.update_closing(
            "org-123", "manager-123", str(closing.closing_id), dto, is_manager=True
        )
        
        # Verify no exception was raised and closing was saved
        assert result is not None
        assert mock_repo.save.called
        assert closing.status == 'approved'

    @patch('app.services.closing_service.ClosingRepository')
    def test_manager_can_reject_closing(self, mock_repo_class):
        """
        Test that a manager can reject a closing.
        
        **Validates: Requirement 5.7**
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        closing = Closing(
            closing_id=uuid.uuid4(),
            organization_id="org-123",
            session_id=uuid.uuid4(),
            assignment_id=uuid.uuid4(),
            branch_id=uuid.uuid4(),
            terminal_id=None,
            cashier_id="cashier-123",
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
        
        mock_repo.find_by_id_and_organization.return_value = closing
        mock_repo.save.return_value = closing
        
        # Manager rejects closing
        dto = ClosingUpdateRequestDTO(status='rejected')
        result = closing_service.update_closing(
            "org-123", "manager-123", str(closing.closing_id), dto, is_manager=True
        )
        
        # Verify no exception was raised and closing was saved
        assert result is not None
        assert mock_repo.save.called
        assert closing.status == 'rejected'

    @patch('app.services.closing_service.ClosingRepository')
    def test_non_manager_cannot_approve_closing(self, mock_repo_class):
        """
        Test that a non-manager cannot approve a closing.
        
        **Validates: Requirement 5.7**
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        closing = Closing(
            closing_id=uuid.uuid4(),
            organization_id="org-123",
            session_id=uuid.uuid4(),
            assignment_id=uuid.uuid4(),
            branch_id=uuid.uuid4(),
            terminal_id=None,
            cashier_id="cashier-123",
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
        
        mock_repo.find_by_id_and_organization.return_value = closing
        
        # Non-manager attempts to approve closing
        dto = ClosingUpdateRequestDTO(status='approved')
        
        with pytest.raises(PermissionError) as exc_info:
            closing_service.update_closing(
                "org-123", "user-123", str(closing.closing_id), dto, is_manager=False
            )
        
        assert "Only managers can approve or reject closings" in str(exc_info.value)
        # Verify save was not called
        assert not mock_repo.save.called

    @patch('app.services.closing_service.ClosingRepository')
    def test_non_manager_cannot_reject_closing(self, mock_repo_class):
        """
        Test that a non-manager cannot reject a closing.
        
        **Validates: Requirement 5.7**
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        closing = Closing(
            closing_id=uuid.uuid4(),
            organization_id="org-123",
            session_id=uuid.uuid4(),
            assignment_id=uuid.uuid4(),
            branch_id=uuid.uuid4(),
            terminal_id=None,
            cashier_id="cashier-123",
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
        
        mock_repo.find_by_id_and_organization.return_value = closing
        
        # Non-manager attempts to reject closing
        dto = ClosingUpdateRequestDTO(status='rejected')
        
        with pytest.raises(PermissionError) as exc_info:
            closing_service.update_closing(
                "org-123", "user-123", str(closing.closing_id), dto, is_manager=False
            )
        
        assert "Only managers can approve or reject closings" in str(exc_info.value)
        # Verify save was not called
        assert not mock_repo.save.called

    @patch('app.services.closing_service.ClosingRepository')
    def test_non_manager_can_update_notes(self, mock_repo_class):
        """
        Test that a non-manager can update notes (non-status fields).
        
        **Validates: Requirement 5.7** (only approval/rejection restricted)
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        closing = Closing(
            closing_id=uuid.uuid4(),
            organization_id="org-123",
            session_id=uuid.uuid4(),
            assignment_id=uuid.uuid4(),
            branch_id=uuid.uuid4(),
            terminal_id=None,
            cashier_id="cashier-123",
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
        
        mock_repo.find_by_id_and_organization.return_value = closing
        mock_repo.save.return_value = closing
        
        # Non-manager updates notes (allowed)
        dto = ClosingUpdateRequestDTO(notes="Updated notes from cashier")
        result = closing_service.update_closing(
            "org-123", "user-123", str(closing.closing_id), dto, is_manager=False
        )
        
        # Verify no exception was raised and closing was saved
        assert result is not None
        assert mock_repo.save.called
        assert closing.notes == "Updated notes from cashier"

    @patch('app.services.closing_service.ClosingRepository')
    def test_non_manager_can_set_status_to_pending(self, mock_repo_class):
        """
        Test that a non-manager can set status to 'pending'.
        
        **Validates: Requirement 5.7** (only approval/rejection restricted)
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        closing = Closing(
            closing_id=uuid.uuid4(),
            organization_id="org-123",
            session_id=uuid.uuid4(),
            assignment_id=uuid.uuid4(),
            branch_id=uuid.uuid4(),
            terminal_id=None,
            cashier_id="cashier-123",
            expected_cash=Decimal('100.00'),
            expected_sinpe=Decimal('50.00'),
            expected_card=Decimal('50.00'),
            expected_total=Decimal('200.00'),
            declared_cash=Decimal('100.00'),
            declared_sinpe=Decimal('50.00'),
            declared_card=Decimal('50.00'),
            declared_total=Decimal('200.00'),
            status='approved',
        )
        
        mock_repo.find_by_id_and_organization.return_value = closing
        mock_repo.save.return_value = closing
        
        # Non-manager sets status to pending (allowed)
        dto = ClosingUpdateRequestDTO(status='pending')
        result = closing_service.update_closing(
            "org-123", "user-123", str(closing.closing_id), dto, is_manager=False
        )
        
        # Verify no exception was raised and closing was saved
        assert result is not None
        assert mock_repo.save.called
        assert closing.status == 'pending'

    @patch('app.services.closing_service.ClosingRepository')
    def test_authorization_check_only_for_approval_rejection(self, mock_repo_class):
        """
        Test that authorization is only checked for 'approved' and 'rejected' statuses.
        
        **Validates: Requirement 5.7** (specific to approval/rejection)
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        closing = Closing(
            closing_id=uuid.uuid4(),
            organization_id="org-123",
            session_id=uuid.uuid4(),
            assignment_id=uuid.uuid4(),
            branch_id=uuid.uuid4(),
            terminal_id=None,
            cashier_id="cashier-123",
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
        
        mock_repo.find_by_id_and_organization.return_value = closing
        mock_repo.save.return_value = closing
        
        # Non-manager can update to pending (no authorization check)
        dto = ClosingUpdateRequestDTO(status='pending')
        result = closing_service.update_closing(
            "org-123", "user-123", str(closing.closing_id), dto, is_manager=False
        )
        assert result is not None
        
        # Non-manager cannot update to approved (authorization check)
        dto = ClosingUpdateRequestDTO(status='approved')
        with pytest.raises(PermissionError):
            closing_service.update_closing(
                "org-123", "user-123", str(closing.closing_id), dto, is_manager=False
            )
        
        # Non-manager cannot update to rejected (authorization check)
        dto = ClosingUpdateRequestDTO(status='rejected')
        with pytest.raises(PermissionError):
            closing_service.update_closing(
                "org-123", "user-123", str(closing.closing_id), dto, is_manager=False
            )

    @patch('app.services.closing_service.ClosingRepository')
    def test_manager_approval_sets_reviewed_fields(self, mock_repo_class):
        """
        Test that manager approval automatically sets reviewed_by and reviewed_at.
        
        **Validates: Requirements 5.5, 5.6**
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        closing = Closing(
            closing_id=uuid.uuid4(),
            organization_id="org-123",
            session_id=uuid.uuid4(),
            assignment_id=uuid.uuid4(),
            branch_id=uuid.uuid4(),
            terminal_id=None,
            cashier_id="cashier-123",
            expected_cash=Decimal('100.00'),
            expected_sinpe=Decimal('50.00'),
            expected_card=Decimal('50.00'),
            expected_total=Decimal('200.00'),
            declared_cash=Decimal('100.00'),
            declared_sinpe=Decimal('50.00'),
            declared_card=Decimal('50.00'),
            declared_total=Decimal('200.00'),
            status='pending',
            reviewed_by=None,
            reviewed_at=None,
        )
        
        mock_repo.find_by_id_and_organization.return_value = closing
        mock_repo.save.return_value = closing
        
        # Manager approves
        dto = ClosingUpdateRequestDTO(status='approved')
        result = closing_service.update_closing(
            "org-123", "manager-123", str(closing.closing_id), dto, is_manager=True
        )
        
        # Verify reviewed fields are set
        assert closing.reviewed_by == "manager-123"
        assert closing.reviewed_at is not None
        assert isinstance(closing.reviewed_at, datetime)

    @patch('app.services.closing_service.ClosingRepository')
    def test_explicit_reviewed_by_overrides_user_id(self, mock_repo_class):
        """
        Test that explicit reviewed_by in DTO overrides the user_id parameter.
        
        **Validates: Requirement 5.5**
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        closing = Closing(
            closing_id=uuid.uuid4(),
            organization_id="org-123",
            session_id=uuid.uuid4(),
            assignment_id=uuid.uuid4(),
            branch_id=uuid.uuid4(),
            terminal_id=None,
            cashier_id="cashier-123",
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
        
        mock_repo.find_by_id_and_organization.return_value = closing
        mock_repo.save.return_value = closing
        
        # Manager approves but specifies different reviewer
        dto = ClosingUpdateRequestDTO(
            status='approved',
            reviewed_by="other-manager-123"
        )
        result = closing_service.update_closing(
            "org-123", "manager-123", str(closing.closing_id), dto, is_manager=True
        )
        
        # Verify reviewed_by uses the explicit value
        assert closing.reviewed_by == "other-manager-123"
