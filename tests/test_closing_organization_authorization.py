"""
Integration tests for organization-scoped authorization on closing operations.
These tests verify that users can only access closings for organizations they belong to.

**Validates: Requirements 8.1, 8.2, 8.4**
- Requirement 8.1: WHEN a user requests data THEN THE System SHALL verify the user is a member of the specified organization
- Requirement 8.2: WHEN a user attempts to create or modify data THEN THE System SHALL verify the user has appropriate permissions for the organization
- Requirement 8.4: THE System SHALL return 403 Forbidden when authorization checks fail
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
from app.dtos.requests.closing_request_dto import (
    ClosingCreateRequestDTO,
    ClosingUpdateRequestDTO,
)


@pytest.mark.integration
class TestClosingOrganizationAuthorization:
    """Integration tests for organization-scoped authorization on closings."""

    @pytest.fixture
    def test_setup(self):
        """Create test data for two different organizations."""
        org1_id = f"test-org-1-{uuid.uuid4()}"
        org2_id = f"test-org-2-{uuid.uuid4()}"
        user1_id = f"test-user-1-{uuid.uuid4()}"
        user2_id = f"test-user-2-{uuid.uuid4()}"
        
        # Create branch for org1
        with BranchRepository() as repo:
            branch1 = Branch(
                branch_id=uuid.uuid4(),
                organization_id=org1_id,
                name="Org1 Branch",
                code=f"O1B-{uuid.uuid4().hex[:6]}",
                type="stand",
                is_active=True,
                created_by=user1_id,
            )
            branch1 = repo.save(branch1)
        
        # Create session for org1
        with SessionRepository() as repo:
            session1 = Session(
                session_id=uuid.uuid4(),
                organization_id=org1_id,
                branch_id=branch1.branch_id,
                name="Org1 Session",
                type="match",
                context="gradas",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user1_id,
            )
            session1 = repo.save(session1)
        
        # Create assignment for org1
        with AssignmentRepository() as repo:
            assignment1 = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org1_id,
                session_id=session1.session_id,
                user_id=user1_id,
                branch_id=branch1.branch_id,
                terminal_id=None,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user1_id,
            )
            assignment1 = repo.save(assignment1)
        
        # Create branch for org2
        with BranchRepository() as repo:
            branch2 = Branch(
                branch_id=uuid.uuid4(),
                organization_id=org2_id,
                name="Org2 Branch",
                code=f"O2B-{uuid.uuid4().hex[:6]}",
                type="restaurant",
                is_active=True,
                created_by=user2_id,
            )
            branch2 = repo.save(branch2)
        
        # Create session for org2
        with SessionRepository() as repo:
            session2 = Session(
                session_id=uuid.uuid4(),
                organization_id=org2_id,
                branch_id=branch2.branch_id,
                name="Org2 Session",
                type="shift",
                context="caja",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user2_id,
            )
            session2 = repo.save(session2)
        
        # Create assignment for org2
        with AssignmentRepository() as repo:
            assignment2 = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org2_id,
                session_id=session2.session_id,
                user_id=user2_id,
                branch_id=branch2.branch_id,
                terminal_id=None,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user2_id,
            )
            assignment2 = repo.save(assignment2)
        
        yield {
            'org1_id': org1_id,
            'org2_id': org2_id,
            'user1_id': user1_id,
            'user2_id': user2_id,
            'branch1': branch1,
            'branch2': branch2,
            'session1': session1,
            'session2': session2,
            'assignment1': assignment1,
            'assignment2': assignment2,
        }
        
        # Cleanup
        with AssignmentRepository() as repo:
            repo.delete(str(assignment1.assignment_id))
            repo.delete(str(assignment2.assignment_id))
        with SessionRepository() as repo:
            repo.delete(str(session1.session_id))
            repo.delete(str(session2.session_id))
        with BranchRepository() as repo:
            repo.delete(str(branch1.branch_id))
            repo.delete(str(branch2.branch_id))

    def test_get_closings_filters_by_organization(self, test_setup):
        """
        Test that get_closings only returns closings for the specified organization.
        
        **Validates: Requirement 8.1**
        WHEN a user requests data THEN THE System SHALL verify the user is a member of the specified organization
        """
        org1_id = test_setup['org1_id']
        org2_id = test_setup['org2_id']
        user1_id = test_setup['user1_id']
        user2_id = test_setup['user2_id']
        assignment1 = test_setup['assignment1']
        assignment2 = test_setup['assignment2']
        session1 = test_setup['session1']
        session2 = test_setup['session2']
        branch1 = test_setup['branch1']
        branch2 = test_setup['branch2']
        
        # Create closing for org1
        with ClosingRepository() as repo:
            closing1 = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org1_id,
                session_id=session1.session_id,
                assignment_id=assignment1.assignment_id,
                branch_id=branch1.branch_id,
                terminal_id=None,
                cashier_id=user1_id,
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
        
        # Create closing for org2
        with ClosingRepository() as repo:
            closing2 = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org2_id,
                session_id=session2.session_id,
                assignment_id=assignment2.assignment_id,
                branch_id=branch2.branch_id,
                terminal_id=None,
                cashier_id=user2_id,
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
        
        # User from org1 requests closings for org1
        closings_org1 = closing_service.get_closings(org1_id, user1_id)
        closing_ids_org1 = [c.closing_id for c in closings_org1]
        
        # Verify org1 closing is returned
        assert str(closing1.closing_id) in closing_ids_org1
        # Verify org2 closing is NOT returned
        assert str(closing2.closing_id) not in closing_ids_org1
        
        # User from org2 requests closings for org2
        closings_org2 = closing_service.get_closings(org2_id, user2_id)
        closing_ids_org2 = [c.closing_id for c in closings_org2]
        
        # Verify org2 closing is returned
        assert str(closing2.closing_id) in closing_ids_org2
        # Verify org1 closing is NOT returned
        assert str(closing1.closing_id) not in closing_ids_org2
        
        # Cleanup
        with ClosingRepository() as repo:
            repo.delete(str(closing1.closing_id))
            repo.delete(str(closing2.closing_id))

    def test_get_closing_enforces_organization_scope(self, test_setup):
        """
        Test that get_closing returns None when accessing a closing from a different organization.
        
        **Validates: Requirement 8.1**
        WHEN a user requests data THEN THE System SHALL verify the user is a member of the specified organization
        """
        org1_id = test_setup['org1_id']
        org2_id = test_setup['org2_id']
        user1_id = test_setup['user1_id']
        user2_id = test_setup['user2_id']
        assignment1 = test_setup['assignment1']
        session1 = test_setup['session1']
        branch1 = test_setup['branch1']
        
        # Create closing for org1
        with ClosingRepository() as repo:
            closing1 = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org1_id,
                session_id=session1.session_id,
                assignment_id=assignment1.assignment_id,
                branch_id=branch1.branch_id,
                terminal_id=None,
                cashier_id=user1_id,
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
        
        closing_id = str(closing1.closing_id)
        
        # User from org1 can access the closing
        result = closing_service.get_closing(org1_id, user1_id, closing_id)
        assert result is not None
        assert result.closing_id == closing_id
        
        # User from org2 cannot access the closing (returns None)
        result = closing_service.get_closing(org2_id, user2_id, closing_id)
        assert result is None
        
        # Cleanup
        with ClosingRepository() as repo:
            repo.delete(closing_id)

    def test_create_closing_validates_assignment_organization(self, test_setup):
        """
        Test that create_closing validates the assignment belongs to the organization.
        
        **Validates: Requirement 8.2**
        WHEN a user attempts to create or modify data THEN THE System SHALL verify the user has appropriate permissions for the organization
        """
        org1_id = test_setup['org1_id']
        org2_id = test_setup['org2_id']
        user1_id = test_setup['user1_id']
        user2_id = test_setup['user2_id']
        assignment1 = test_setup['assignment1']
        
        # Try to create closing for org1's assignment using org2's context
        dto = ClosingCreateRequestDTO(
            assignment_id=str(assignment1.assignment_id),
            declared_cash=Decimal('100.00'),
            declared_sinpe=Decimal('50.00'),
            declared_card=Decimal('50.00'),
            notes="Test closing",
        )
        
        # Should fail because assignment belongs to org1, not org2
        with pytest.raises(ValueError) as exc_info:
            closing_service.create_closing(org2_id, user2_id, dto)
        
        assert "does not exist or does not belong to this organization" in str(exc_info.value)
        
        # Should succeed when using correct organization
        result = closing_service.create_closing(org1_id, user1_id, dto)
        assert result is not None
        assert result.organization_id == org1_id
        
        # Cleanup
        with ClosingRepository() as repo:
            repo.delete(result.closing_id)

    def test_update_closing_enforces_organization_scope(self, test_setup):
        """
        Test that update_closing only updates closings within the specified organization.
        
        **Validates: Requirement 8.2**
        WHEN a user attempts to create or modify data THEN THE System SHALL verify the user has appropriate permissions for the organization
        """
        org1_id = test_setup['org1_id']
        org2_id = test_setup['org2_id']
        user1_id = test_setup['user1_id']
        user2_id = test_setup['user2_id']
        assignment1 = test_setup['assignment1']
        session1 = test_setup['session1']
        branch1 = test_setup['branch1']
        
        # Create closing for org1
        with ClosingRepository() as repo:
            closing1 = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org1_id,
                session_id=session1.session_id,
                assignment_id=assignment1.assignment_id,
                branch_id=branch1.branch_id,
                terminal_id=None,
                cashier_id=user1_id,
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
        
        closing_id = str(closing1.closing_id)
        
        # User from org1 can update the closing
        dto = ClosingUpdateRequestDTO(notes="Updated by org1 user")
        result = closing_service.update_closing(org1_id, user1_id, closing_id, dto, is_manager=True)
        assert result is not None
        assert result.notes == "Updated by org1 user"
        
        # User from org2 cannot update the closing (returns None)
        dto = ClosingUpdateRequestDTO(notes="Attempted update by org2 user")
        result = closing_service.update_closing(org2_id, user2_id, closing_id, dto, is_manager=True)
        assert result is None
        
        # Verify the closing was not modified by org2 user
        result = closing_service.get_closing(org1_id, user1_id, closing_id)
        assert result.notes == "Updated by org1 user"
        
        # Cleanup
        with ClosingRepository() as repo:
            repo.delete(closing_id)

    def test_delete_closing_enforces_organization_scope(self, test_setup):
        """
        Test that delete_closing only deletes closings within the specified organization.
        
        **Validates: Requirement 8.2**
        WHEN a user attempts to create or modify data THEN THE System SHALL verify the user has appropriate permissions for the organization
        """
        org1_id = test_setup['org1_id']
        org2_id = test_setup['org2_id']
        user1_id = test_setup['user1_id']
        user2_id = test_setup['user2_id']
        assignment1 = test_setup['assignment1']
        session1 = test_setup['session1']
        branch1 = test_setup['branch1']
        
        # Create closing for org1
        with ClosingRepository() as repo:
            closing1 = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org1_id,
                session_id=session1.session_id,
                assignment_id=assignment1.assignment_id,
                branch_id=branch1.branch_id,
                terminal_id=None,
                cashier_id=user1_id,
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
        
        closing_id = str(closing1.closing_id)
        
        # User from org2 cannot delete the closing (returns False)
        success = closing_service.delete_closing(org2_id, user2_id, closing_id)
        assert success is False
        
        # Verify the closing still exists
        result = closing_service.get_closing(org1_id, user1_id, closing_id)
        assert result is not None
        
        # User from org1 can delete the closing
        success = closing_service.delete_closing(org1_id, user1_id, closing_id)
        assert success is True
        
        # Verify the closing is deleted
        result = closing_service.get_closing(org1_id, user1_id, closing_id)
        assert result is None

    def test_repository_find_by_id_and_organization(self, test_setup):
        """
        Test that repository method find_by_id_and_organization filters by organization_id.
        
        **Validates: Requirement 8.1**
        WHEN a user requests data THEN THE System SHALL verify the user is a member of the specified organization
        """
        org1_id = test_setup['org1_id']
        org2_id = test_setup['org2_id']
        user1_id = test_setup['user1_id']
        assignment1 = test_setup['assignment1']
        session1 = test_setup['session1']
        branch1 = test_setup['branch1']
        
        # Create closing for org1
        with ClosingRepository() as repo:
            closing1 = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org1_id,
                session_id=session1.session_id,
                assignment_id=assignment1.assignment_id,
                branch_id=branch1.branch_id,
                terminal_id=None,
                cashier_id=user1_id,
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
        
        closing_id = str(closing1.closing_id)
        
        # Repository method returns closing when organization matches
        with ClosingRepository() as repo:
            result = repo.find_by_id_and_organization(closing_id, org1_id)
            assert result is not None
            assert str(result.closing_id) == closing_id
        
        # Repository method returns None when organization doesn't match
        with ClosingRepository() as repo:
            result = repo.find_by_id_and_organization(closing_id, org2_id)
            assert result is None
        
        # Cleanup
        with ClosingRepository() as repo:
            repo.delete(closing_id)

    def test_repository_find_all_by_organization(self, test_setup):
        """
        Test that repository method find_all_by_organization filters by organization_id.
        
        **Validates: Requirement 8.1**
        WHEN a user requests data THEN THE System SHALL verify the user is a member of the specified organization
        """
        org1_id = test_setup['org1_id']
        org2_id = test_setup['org2_id']
        user1_id = test_setup['user1_id']
        user2_id = test_setup['user2_id']
        assignment1 = test_setup['assignment1']
        assignment2 = test_setup['assignment2']
        session1 = test_setup['session1']
        session2 = test_setup['session2']
        branch1 = test_setup['branch1']
        branch2 = test_setup['branch2']
        
        # Create closings for both organizations
        with ClosingRepository() as repo:
            closing1 = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org1_id,
                session_id=session1.session_id,
                assignment_id=assignment1.assignment_id,
                branch_id=branch1.branch_id,
                terminal_id=None,
                cashier_id=user1_id,
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
            
            closing2 = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org2_id,
                session_id=session2.session_id,
                assignment_id=assignment2.assignment_id,
                branch_id=branch2.branch_id,
                terminal_id=None,
                cashier_id=user2_id,
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
        
        # Repository method returns only org1 closings
        with ClosingRepository() as repo:
            closings = repo.find_all_by_organization(org1_id)
            closing_ids = [str(c.closing_id) for c in closings]
            assert str(closing1.closing_id) in closing_ids
            assert str(closing2.closing_id) not in closing_ids
        
        # Repository method returns only org2 closings
        with ClosingRepository() as repo:
            closings = repo.find_all_by_organization(org2_id)
            closing_ids = [str(c.closing_id) for c in closings]
            assert str(closing2.closing_id) in closing_ids
            assert str(closing1.closing_id) not in closing_ids
        
        # Cleanup
        with ClosingRepository() as repo:
            repo.delete(str(closing1.closing_id))
            repo.delete(str(closing2.closing_id))

    def test_repository_validate_assignment_exists_checks_organization(self, test_setup):
        """
        Test that repository method validate_assignment_exists checks organization_id.
        
        **Validates: Requirement 8.2**
        WHEN a user attempts to create or modify data THEN THE System SHALL verify the user has appropriate permissions for the organization
        """
        org1_id = test_setup['org1_id']
        org2_id = test_setup['org2_id']
        assignment1 = test_setup['assignment1']
        
        # Assignment exists in org1
        with ClosingRepository() as repo:
            exists = repo.validate_assignment_exists(str(assignment1.assignment_id), org1_id)
            assert exists is True
        
        # Assignment does not exist in org2
        with ClosingRepository() as repo:
            exists = repo.validate_assignment_exists(str(assignment1.assignment_id), org2_id)
            assert exists is False
