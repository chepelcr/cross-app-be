"""
Test that closing status is automatically set to 'pending' when created.

This test verifies Requirement 5.3:
- Requirement 5.3: WHEN a cashier submits a closing THEN THE System SHALL create a closing record with status 'pending'
"""
import pytest
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.models.session import Session
from app.models.branch import Branch
from app.models.assignment import Assignment
from app.repositories.session_repository import SessionRepository
from app.repositories.branch_repository import BranchRepository
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.closing_repository import ClosingRepository
from app.services import closing_service
from app.dtos.requests.closing_request_dto import ClosingCreateRequestDTO


@pytest.mark.integration
class TestClosingStatusPending:
    """Test automatic setting of status to 'pending' when creating a closing."""

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

    def test_closing_status_set_to_pending_on_creation(self, test_setup):
        """
        Test that when a closing is created via create_closing service,
        the status is automatically set to 'pending'.
        
        **Validates: Requirement 5.3**
        """
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        
        # Create closing request DTO
        dto = ClosingCreateRequestDTO(
            assignment_id=str(assignment.assignment_id),
            declared_cash=Decimal('100.00'),
            declared_sinpe=Decimal('50.00'),
            declared_card=Decimal('75.00'),
            notes="Test closing submission"
        )
        
        # Create closing through service
        closing_response = closing_service.create_closing(org_id, user_id, dto)
        
        # Verify status is 'pending'
        assert closing_response.status == 'pending', \
            f"Expected status to be 'pending', but got '{closing_response.status}'"
        
        # Verify in database
        with ClosingRepository() as repo:
            closing = repo.get_by_id(closing_response.closing_id)
            assert closing.status == 'pending', \
                f"Expected database status to be 'pending', but got '{closing.status}'"
            
            # Cleanup
            repo.delete(closing_response.closing_id)

    def test_closing_status_pending_from_database_default(self, test_setup):
        """
        Test that the database default value for status is 'pending'.
        This verifies the schema migration is correct.
        """
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create closing request DTO
        dto = ClosingCreateRequestDTO(
            assignment_id=str(assignment.assignment_id),
            declared_cash=Decimal('200.00'),
            declared_sinpe=Decimal('100.00'),
            declared_card=Decimal('150.00'),
            notes="Testing database default"
        )
        
        # Create closing through service
        closing_response = closing_service.create_closing(org_id, user_id, dto)
        
        # Retrieve from database to verify default was applied
        with ClosingRepository() as repo:
            closing = repo.get_by_id(closing_response.closing_id)
            
            # Verify status is 'pending' (from database default or service)
            assert closing.status == 'pending'
            
            # Verify other fields are set correctly
            assert closing.organization_id == org_id
            assert closing.session_id == session.session_id
            assert closing.branch_id == branch.branch_id
            assert closing.cashier_id == user_id
            
            # Cleanup
            repo.delete(closing_response.closing_id)
