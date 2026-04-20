"""
Test that closing differences are calculated automatically by the database.

This test verifies Requirement 5.2 and 9.5:
- Requirement 5.2: System SHALL calculate differences between declared and expected amounts
- Requirement 9.5: System SHALL use generated columns for calculated fields (closing differences)
"""
import pytest
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.models.closing import Closing
from app.models.session import Session
from app.models.branch import Branch
from app.models.assignment import Assignment
from app.repositories.closing_repository import ClosingRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.branch_repository import BranchRepository
from app.repositories.assignment_repository import AssignmentRepository


@pytest.mark.integration
class TestClosingDifferenceCalculation:
    """Test automatic calculation of closing differences using database generated columns."""

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

    def test_differences_calculated_automatically_exact_match(self, test_setup):
        """Test that differences are zero when declared equals expected."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create closing with matching amounts
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
                expected_card=Decimal('75.00'),
                expected_total=Decimal('225.00'),
                declared_cash=Decimal('100.00'),
                declared_sinpe=Decimal('50.00'),
                declared_card=Decimal('75.00'),
                declared_total=Decimal('225.00'),
                status='pending',
            )
            closing = repo.save(closing)
            
            # Retrieve the closing to get calculated differences
            retrieved = repo.get_by_id(str(closing.closing_id))
            
            # Verify differences are zero
            assert retrieved.cash_difference == Decimal('0.00')
            assert retrieved.sinpe_difference == Decimal('0.00')
            assert retrieved.card_difference == Decimal('0.00')
            assert retrieved.total_difference == Decimal('0.00')
            
            # Cleanup
            repo.delete(str(closing.closing_id))

    def test_differences_calculated_automatically_positive_difference(self, test_setup):
        """Test that positive differences are calculated when declared > expected."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create closing with declared > expected (surplus)
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
                expected_card=Decimal('75.00'),
                expected_total=Decimal('225.00'),
                declared_cash=Decimal('120.00'),  # +20
                declared_sinpe=Decimal('60.00'),   # +10
                declared_card=Decimal('85.00'),    # +10
                declared_total=Decimal('265.00'),  # +40
                status='pending',
            )
            closing = repo.save(closing)
            
            # Retrieve the closing to get calculated differences
            retrieved = repo.get_by_id(str(closing.closing_id))
            
            # Verify differences are positive (surplus)
            assert retrieved.cash_difference == Decimal('20.00')
            assert retrieved.sinpe_difference == Decimal('10.00')
            assert retrieved.card_difference == Decimal('10.00')
            assert retrieved.total_difference == Decimal('40.00')
            
            # Cleanup
            repo.delete(str(closing.closing_id))

    def test_differences_calculated_automatically_negative_difference(self, test_setup):
        """Test that negative differences are calculated when declared < expected."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create closing with declared < expected (shortage)
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
                expected_card=Decimal('75.00'),
                expected_total=Decimal('225.00'),
                declared_cash=Decimal('90.00'),   # -10
                declared_sinpe=Decimal('45.00'),  # -5
                declared_card=Decimal('70.00'),   # -5
                declared_total=Decimal('205.00'), # -20
                status='pending',
            )
            closing = repo.save(closing)
            
            # Retrieve the closing to get calculated differences
            retrieved = repo.get_by_id(str(closing.closing_id))
            
            # Verify differences are negative (shortage)
            assert retrieved.cash_difference == Decimal('-10.00')
            assert retrieved.sinpe_difference == Decimal('-5.00')
            assert retrieved.card_difference == Decimal('-5.00')
            assert retrieved.total_difference == Decimal('-20.00')
            
            # Cleanup
            repo.delete(str(closing.closing_id))

    def test_differences_calculated_automatically_mixed_differences(self, test_setup):
        """Test that differences can be mixed (some positive, some negative)."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create closing with mixed differences
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
                expected_card=Decimal('75.00'),
                expected_total=Decimal('225.00'),
                declared_cash=Decimal('110.00'),  # +10 (surplus)
                declared_sinpe=Decimal('45.00'),  # -5 (shortage)
                declared_card=Decimal('75.00'),   # 0 (exact)
                declared_total=Decimal('230.00'), # +5 (surplus)
                status='pending',
            )
            closing = repo.save(closing)
            
            # Retrieve the closing to get calculated differences
            retrieved = repo.get_by_id(str(closing.closing_id))
            
            # Verify mixed differences
            assert retrieved.cash_difference == Decimal('10.00')
            assert retrieved.sinpe_difference == Decimal('-5.00')
            assert retrieved.card_difference == Decimal('0.00')
            assert retrieved.total_difference == Decimal('5.00')
            
            # Cleanup
            repo.delete(str(closing.closing_id))

    def test_differences_persist_after_update(self, test_setup):
        """Test that differences are recalculated when declared amounts are updated."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create closing with initial amounts
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
                expected_card=Decimal('75.00'),
                expected_total=Decimal('225.00'),
                declared_cash=Decimal('100.00'),
                declared_sinpe=Decimal('50.00'),
                declared_card=Decimal('75.00'),
                declared_total=Decimal('225.00'),
                status='pending',
            )
            closing = repo.save(closing)
            closing_id = str(closing.closing_id)
            
            # Verify initial differences are zero
            retrieved = repo.get_by_id(closing_id)
            assert retrieved.cash_difference == Decimal('0.00')
            
            # Update declared amounts
            retrieved.declared_cash = Decimal('110.00')
            retrieved.declared_total = Decimal('235.00')
            updated = repo.update(closing_id, retrieved)
            
            # Retrieve again to get recalculated differences
            retrieved = repo.get_by_id(closing_id)
            
            # Verify differences are recalculated
            assert retrieved.cash_difference == Decimal('10.00')
            assert retrieved.sinpe_difference == Decimal('0.00')
            assert retrieved.card_difference == Decimal('0.00')
            assert retrieved.total_difference == Decimal('10.00')
            
            # Cleanup
            repo.delete(closing_id)

    def test_differences_with_decimal_precision(self, test_setup):
        """Test that differences maintain decimal precision correctly."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create closing with precise decimal amounts
        with ClosingRepository() as repo:
            closing = Closing(
                closing_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                assignment_id=assignment.assignment_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                cashier_id=user_id,
                expected_cash=Decimal('123.45'),
                expected_sinpe=Decimal('67.89'),
                expected_card=Decimal('234.56'),
                expected_total=Decimal('425.90'),
                declared_cash=Decimal('123.50'),
                declared_sinpe=Decimal('67.80'),
                declared_card=Decimal('234.60'),
                declared_total=Decimal('425.90'),
                status='pending',
            )
            closing = repo.save(closing)
            
            # Retrieve the closing to get calculated differences
            retrieved = repo.get_by_id(str(closing.closing_id))
            
            # Verify differences maintain precision
            assert retrieved.cash_difference == Decimal('0.05')
            assert retrieved.sinpe_difference == Decimal('-0.09')
            assert retrieved.card_difference == Decimal('0.04')
            assert retrieved.total_difference == Decimal('0.00')
            
            # Cleanup
            repo.delete(str(closing.closing_id))
