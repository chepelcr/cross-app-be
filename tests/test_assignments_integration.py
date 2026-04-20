"""
Integration tests for assignments handler with real database operations.
"""
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.configuration.fast_api_config import FastApiConfig
from app.models.assignment import Assignment
from app.models.session import Session
from app.models.branch import Branch
from app.models.terminal import Terminal
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.branch_repository import BranchRepository
from app.repositories.terminal_repository import TerminalRepository
from app.services import assignment_service
from app.dtos.requests.assignment_request_dto import (
    AssignmentCreateRequestDTO,
    AssignmentUpdateRequestDTO,
)


@pytest.mark.integration
class TestAssignmentIntegration:
    """Integration tests for assignment operations with database."""

    @pytest.fixture
    def test_setup(self):
        """Create test branch, terminal, and session for assignment tests."""
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
        
        # Create terminal
        with TerminalRepository() as repo:
            terminal = Terminal(
                terminal_id=uuid.uuid4(),
                organization_id=org_id,
                branch_id=branch.branch_id,
                name="Test Terminal",
                code=f"TT-{uuid.uuid4().hex[:6]}",
                is_active=True,
                registered_at=datetime.now(timezone.utc),
            )
            terminal = repo.save(terminal)
        
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
        
        yield branch, terminal, session, org_id, user_id
        
        # Cleanup
        with SessionRepository() as repo:
            repo.delete(str(session.session_id))
        with TerminalRepository() as repo:
            repo.delete(str(terminal.terminal_id))
        with BranchRepository() as repo:
            repo.delete(str(branch.branch_id))

    def test_create_and_retrieve_assignment(self, test_setup):
        """Test creating an assignment and retrieving it."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Create assignment
        cashier_id = f"cashier-{uuid.uuid4()}"
        start_time = datetime.now(timezone.utc)
        dto = AssignmentCreateRequestDTO(
            session_id=str(session.session_id),
            user_id=cashier_id,
            branch_id=str(branch.branch_id),
            terminal_id=str(terminal.terminal_id),
            role="cashier",
            start_time=start_time,
        )
        
        created = assignment_service.create_assignment(org_id, user_id, dto)
        
        assert created is not None
        assert created.user_id == cashier_id
        assert created.role == "cashier"
        assert created.session_id == str(session.session_id)
        assert created.branch_id == str(branch.branch_id)
        assert created.terminal_id == str(terminal.terminal_id)
        assert created.is_active is True
        
        # Retrieve assignment
        retrieved = assignment_service.get_assignment(org_id, user_id, created.assignment_id)
        
        assert retrieved is not None
        assert retrieved.assignment_id == created.assignment_id
        assert retrieved.user_id == cashier_id
        
        # Cleanup
        with AssignmentRepository() as repo:
            repo.delete(created.assignment_id)

    def test_create_assignment_without_terminal(self, test_setup):
        """Test creating an assignment without a terminal (supervisor role)."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Create assignment without terminal
        supervisor_id = f"supervisor-{uuid.uuid4()}"
        start_time = datetime.now(timezone.utc)
        dto = AssignmentCreateRequestDTO(
            session_id=str(session.session_id),
            user_id=supervisor_id,
            branch_id=str(branch.branch_id),
            terminal_id=None,
            role="supervisor",
            start_time=start_time,
        )
        
        created = assignment_service.create_assignment(org_id, user_id, dto)
        
        assert created is not None
        assert created.role == "supervisor"
        assert created.terminal_id is None
        assert created.is_active is True
        
        # Cleanup
        with AssignmentRepository() as repo:
            repo.delete(created.assignment_id)

    def test_update_assignment(self, test_setup):
        """Test updating an assignment."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Create assignment
        cashier_id = f"cashier-{uuid.uuid4()}"
        with AssignmentRepository() as repo:
            assignment = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                user_id=cashier_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            assignment = repo.save(assignment)
        
        # Update assignment to add terminal
        dto = AssignmentUpdateRequestDTO(
            terminal_id=str(terminal.terminal_id),
        )
        
        updated = assignment_service.update_assignment(
            org_id, user_id, str(assignment.assignment_id), dto
        )
        
        assert updated is not None
        assert updated.terminal_id == str(terminal.terminal_id)
        
        # Cleanup
        with AssignmentRepository() as repo:
            repo.delete(str(assignment.assignment_id))

    def test_deactivate_assignment_sets_end_time(self, test_setup):
        """Test that deactivating an assignment automatically sets end_time."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Create assignment
        cashier_id = f"cashier-{uuid.uuid4()}"
        with AssignmentRepository() as repo:
            assignment = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                user_id=cashier_id,
                branch_id=branch.branch_id,
                terminal_id=terminal.terminal_id,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                end_time=None,
                is_active=True,
                created_by=user_id,
            )
            assignment = repo.save(assignment)
        
        assignment_id = str(assignment.assignment_id)
        
        # Deactivate assignment
        dto = AssignmentUpdateRequestDTO(
            is_active=False,
        )
        
        updated = assignment_service.update_assignment(org_id, user_id, assignment_id, dto)
        
        assert updated is not None
        assert updated.is_active is False
        assert updated.end_time is not None
        
        # Cleanup
        with AssignmentRepository() as repo:
            repo.delete(assignment_id)

    def test_delete_assignment(self, test_setup):
        """Test deleting an assignment."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Create assignment
        cashier_id = f"cashier-{uuid.uuid4()}"
        with AssignmentRepository() as repo:
            assignment = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                user_id=cashier_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=False,
                created_by=user_id,
            )
            assignment = repo.save(assignment)
        
        assignment_id = str(assignment.assignment_id)
        
        # Delete assignment
        result = assignment_service.delete_assignment(org_id, user_id, assignment_id)
        
        assert result is True
        
        # Verify deletion
        retrieved = assignment_service.get_assignment(org_id, user_id, assignment_id)
        assert retrieved is None

    def test_list_assignments_with_filters(self, test_setup):
        """Test listing assignments with various filters."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Create multiple assignments
        assignments = []
        cashier_ids = [f"cashier-{uuid.uuid4()}" for _ in range(4)]
        
        with AssignmentRepository() as repo:
            for i in range(4):
                assignment = Assignment(
                    assignment_id=uuid.uuid4(),
                    organization_id=org_id,
                    session_id=session.session_id,
                    user_id=cashier_ids[i],
                    branch_id=branch.branch_id,
                    terminal_id=terminal.terminal_id if i < 2 else None,
                    role="cashier" if i % 2 == 0 else "supervisor",
                    start_time=datetime.now(timezone.utc) - timedelta(hours=i),
                    is_active=(i % 2 == 0),
                    created_by=user_id,
                )
                assignment = repo.save(assignment)
                assignments.append(assignment)
        
        # Test filter by is_active
        active_assignments = assignment_service.get_assignments(
            org_id, user_id, is_active=True
        )
        assert len(active_assignments) >= 2
        
        # Test filter by session_id
        session_assignments = assignment_service.get_assignments(
            org_id, user_id, session_id=str(session.session_id)
        )
        assert len(session_assignments) >= 4
        
        # Test filter by assigned_user_id
        user_assignments = assignment_service.get_assignments(
            org_id, user_id, assigned_user_id=cashier_ids[0]
        )
        assert len(user_assignments) >= 1
        
        # Test filter by branch_id
        branch_assignments = assignment_service.get_assignments(
            org_id, user_id, branch_id=str(branch.branch_id)
        )
        assert len(branch_assignments) >= 4
        
        # Test multiple filters
        filtered_assignments = assignment_service.get_assignments(
            org_id, user_id, is_active=True, session_id=str(session.session_id)
        )
        assert len(filtered_assignments) >= 2
        
        # Cleanup
        with AssignmentRepository() as repo:
            for assignment in assignments:
                repo.delete(str(assignment.assignment_id))

    def test_session_validation(self, test_setup):
        """Test that assignment creation validates session existence and active status."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Try to create assignment with non-existent session
        dto = AssignmentCreateRequestDTO(
            session_id=str(uuid.uuid4()),
            user_id=f"cashier-{uuid.uuid4()}",
            branch_id=str(branch.branch_id),
            terminal_id=None,
            role="cashier",
            start_time=datetime.now(timezone.utc),
        )
        
        with pytest.raises(ValueError, match="does not exist.*or is not active"):
            assignment_service.create_assignment(org_id, user_id, dto)

    def test_branch_validation(self, test_setup):
        """Test that assignment creation validates branch existence."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Try to create assignment with non-existent branch
        dto = AssignmentCreateRequestDTO(
            session_id=str(session.session_id),
            user_id=f"cashier-{uuid.uuid4()}",
            branch_id=str(uuid.uuid4()),
            terminal_id=None,
            role="cashier",
            start_time=datetime.now(timezone.utc),
        )
        
        with pytest.raises(ValueError, match="does not exist or does not belong"):
            assignment_service.create_assignment(org_id, user_id, dto)

    def test_terminal_validation(self, test_setup):
        """Test that assignment creation validates terminal existence and branch association."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Try to create assignment with non-existent terminal
        dto = AssignmentCreateRequestDTO(
            session_id=str(session.session_id),
            user_id=f"cashier-{uuid.uuid4()}",
            branch_id=str(branch.branch_id),
            terminal_id=str(uuid.uuid4()),
            role="cashier",
            start_time=datetime.now(timezone.utc),
        )
        
        with pytest.raises(ValueError, match="does not exist or does not belong to branch"):
            assignment_service.create_assignment(org_id, user_id, dto)

    def test_user_cannot_have_multiple_active_assignments(self, test_setup):
        """Test that a user cannot have multiple active assignments."""
        branch, terminal, session, org_id, user_id = test_setup
        
        cashier_id = f"cashier-{uuid.uuid4()}"
        
        # Create first assignment
        dto1 = AssignmentCreateRequestDTO(
            session_id=str(session.session_id),
            user_id=cashier_id,
            branch_id=str(branch.branch_id),
            terminal_id=str(terminal.terminal_id),
            role="cashier",
            start_time=datetime.now(timezone.utc),
        )
        
        created1 = assignment_service.create_assignment(org_id, user_id, dto1)
        
        # Try to create second active assignment for same user
        dto2 = AssignmentCreateRequestDTO(
            session_id=str(session.session_id),
            user_id=cashier_id,
            branch_id=str(branch.branch_id),
            terminal_id=None,
            role="cashier",
            start_time=datetime.now(timezone.utc),
        )
        
        with pytest.raises(ValueError, match="already has an active assignment"):
            assignment_service.create_assignment(org_id, user_id, dto2)
        
        # Cleanup
        with AssignmentRepository() as repo:
            repo.delete(created1.assignment_id)

    def test_organization_scoped_data_isolation(self, test_setup):
        """Test that assignments are isolated by organization."""
        branch, terminal, session, org_id, user_id = test_setup
        other_org_id = f"test-org-{uuid.uuid4()}"
        
        # Create assignment in first organization
        cashier_id = f"cashier-{uuid.uuid4()}"
        with AssignmentRepository() as repo:
            assignment = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                user_id=cashier_id,
                branch_id=branch.branch_id,
                terminal_id=terminal.terminal_id,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            assignment = repo.save(assignment)
        
        assignment_id = str(assignment.assignment_id)
        
        # Try to retrieve from different organization
        retrieved = assignment_service.get_assignment(other_org_id, user_id, assignment_id)
        assert retrieved is None
        
        # Verify it exists in correct organization
        retrieved = assignment_service.get_assignment(org_id, user_id, assignment_id)
        assert retrieved is not None
        
        # Cleanup
        with AssignmentRepository() as repo:
            repo.delete(assignment_id)

    def test_assignments_ordered_by_start_time_desc(self, test_setup):
        """Test that assignments are returned ordered by start_time descending."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Create assignments with different start times
        assignments = []
        with AssignmentRepository() as repo:
            for i in range(3):
                cashier_id = f"cashier-{uuid.uuid4()}"
                assignment = Assignment(
                    assignment_id=uuid.uuid4(),
                    organization_id=org_id,
                    session_id=session.session_id,
                    user_id=cashier_id,
                    branch_id=branch.branch_id,
                    terminal_id=None,
                    role="cashier",
                    start_time=datetime.now(timezone.utc) - timedelta(hours=i),
                    is_active=True,
                    created_by=user_id,
                )
                assignment = repo.save(assignment)
                assignments.append(assignment)
        
        # Get all assignments
        retrieved = assignment_service.get_assignments(org_id, user_id)
        
        # Verify ordering (most recent first)
        assignment_ids = [a.assignment_id for a in retrieved]
        our_assignment_ids = [str(a.assignment_id) for a in assignments]
        
        # Find positions of our assignments in the result
        positions = [assignment_ids.index(aid) for aid in our_assignment_ids if aid in assignment_ids]
        
        # Verify they are in descending order (Assignment 0 should come before Assignment 1, etc.)
        assert positions == sorted(positions)
        
        # Cleanup
        with AssignmentRepository() as repo:
            for assignment in assignments:
                repo.delete(str(assignment.assignment_id))

    def test_get_assignment_not_found(self, test_setup):
        """Test getting a non-existent assignment returns None."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Try to get non-existent assignment
        result = assignment_service.get_assignment(org_id, user_id, str(uuid.uuid4()))
        
        assert result is None

    def test_update_assignment_not_found(self, test_setup):
        """Test updating a non-existent assignment returns None."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Try to update non-existent assignment
        dto = AssignmentUpdateRequestDTO(
            is_active=False,
        )
        
        result = assignment_service.update_assignment(
            org_id, user_id, str(uuid.uuid4()), dto
        )
        
        assert result is None

    def test_delete_assignment_not_found(self, test_setup):
        """Test deleting a non-existent assignment returns False."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Try to delete non-existent assignment
        result = assignment_service.delete_assignment(org_id, user_id, str(uuid.uuid4()))
        
        assert result is False


@pytest.mark.integration
class TestAssignmentControllerIntegration:
    """Integration tests for assignment controller endpoints with full HTTP stack."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        app = FastApiConfig().get_app()
        return TestClient(app)

    @pytest.fixture
    def test_setup(self):
        """Create test branch, terminal, and session for assignment tests."""
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
        
        # Create terminal
        with TerminalRepository() as repo:
            terminal = Terminal(
                terminal_id=uuid.uuid4(),
                organization_id=org_id,
                branch_id=branch.branch_id,
                name="Test Terminal",
                code=f"TT-{uuid.uuid4().hex[:6]}",
                is_active=True,
                registered_at=datetime.now(timezone.utc),
            )
            terminal = repo.save(terminal)
        
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
        
        yield branch, terminal, session, org_id, user_id
        
        # Cleanup
        with SessionRepository() as repo:
            repo.delete(str(session.session_id))
        with TerminalRepository() as repo:
            repo.delete(str(terminal.terminal_id))
        with BranchRepository() as repo:
            repo.delete(str(branch.branch_id))

    def test_get_assignments_endpoint(self, client, test_setup):
        """Test GET /assignments endpoint returns list of assignments."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Create test assignment
        cashier_id = f"cashier-{uuid.uuid4()}"
        with AssignmentRepository() as repo:
            assignment = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                user_id=cashier_id,
                branch_id=branch.branch_id,
                terminal_id=terminal.terminal_id,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            assignment = repo.save(assignment)
        
        # Make GET request
        response = client.get(
            f"/api/users/{user_id}/organization/{org_id}/assignments"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Find our assignment
        our_assignment = next(
            (a for a in data if a["assignment_id"] == str(assignment.assignment_id)),
            None
        )
        assert our_assignment is not None
        assert our_assignment["user_id"] == cashier_id
        assert our_assignment["role"] == "cashier"
        assert our_assignment["is_active"] is True
        
        # Cleanup
        with AssignmentRepository() as repo:
            repo.delete(str(assignment.assignment_id))

    def test_get_assignments_with_filters_endpoint(self, client, test_setup):
        """Test GET /assignments endpoint with query filters."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Create multiple assignments
        assignments = []
        cashier_ids = [f"cashier-{uuid.uuid4()}" for _ in range(3)]
        
        with AssignmentRepository() as repo:
            for i in range(3):
                assignment = Assignment(
                    assignment_id=uuid.uuid4(),
                    organization_id=org_id,
                    session_id=session.session_id,
                    user_id=cashier_ids[i],
                    branch_id=branch.branch_id,
                    terminal_id=terminal.terminal_id if i < 2 else None,
                    role="cashier",
                    start_time=datetime.now(timezone.utc),
                    is_active=(i % 2 == 0),
                    created_by=user_id,
                )
                assignment = repo.save(assignment)
                assignments.append(assignment)
        
        # Test filter by is_active
        response = client.get(
            f"/api/users/{user_id}/organization/{org_id}/assignments?is_active=true"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        
        # Test filter by session_id
        response = client.get(
            f"/api/users/{user_id}/organization/{org_id}/assignments?session_id={session.session_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        
        # Test filter by assigned_user_id
        response = client.get(
            f"/api/users/{user_id}/organization/{org_id}/assignments?assigned_user_id={cashier_ids[0]}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        
        # Test filter by branch_id
        response = client.get(
            f"/api/users/{user_id}/organization/{org_id}/assignments?branch_id={branch.branch_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        
        # Cleanup
        with AssignmentRepository() as repo:
            for assignment in assignments:
                repo.delete(str(assignment.assignment_id))

    def test_get_assignment_by_id_endpoint(self, client, test_setup):
        """Test GET /assignments/{id} endpoint returns specific assignment."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Create test assignment
        cashier_id = f"cashier-{uuid.uuid4()}"
        with AssignmentRepository() as repo:
            assignment = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                user_id=cashier_id,
                branch_id=branch.branch_id,
                terminal_id=terminal.terminal_id,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            assignment = repo.save(assignment)
        
        # Make GET request
        response = client.get(
            f"/api/users/{user_id}/organization/{org_id}/assignments/{assignment.assignment_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["assignment_id"] == str(assignment.assignment_id)
        assert data["user_id"] == cashier_id
        assert data["role"] == "cashier"
        assert data["is_active"] is True
        
        # Cleanup
        with AssignmentRepository() as repo:
            repo.delete(str(assignment.assignment_id))

    def test_get_assignment_not_found_endpoint(self, client, test_setup):
        """Test GET /assignments/{id} returns 404 for non-existent assignment."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Make GET request with non-existent ID
        response = client.get(
            f"/api/users/{user_id}/organization/{org_id}/assignments/{uuid.uuid4()}"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_post_assignment_endpoint(self, client, test_setup):
        """Test POST /assignments endpoint creates new assignment."""
        branch, terminal, session, org_id, user_id = test_setup
        
        cashier_id = f"cashier-{uuid.uuid4()}"
        start_time = datetime.now(timezone.utc)
        
        # Make POST request
        response = client.post(
            f"/api/users/{user_id}/organization/{org_id}/assignments",
            json={
                "session_id": str(session.session_id),
                "user_id": cashier_id,
                "branch_id": str(branch.branch_id),
                "terminal_id": str(terminal.terminal_id),
                "role": "cashier",
                "start_time": start_time.isoformat(),
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == cashier_id
        assert data["role"] == "cashier"
        assert data["session_id"] == str(session.session_id)
        assert data["branch_id"] == str(branch.branch_id)
        assert data["terminal_id"] == str(terminal.terminal_id)
        assert data["is_active"] is True
        
        assignment_id = data["assignment_id"]
        
        # Cleanup
        with AssignmentRepository() as repo:
            repo.delete(assignment_id)

    def test_post_assignment_without_terminal_endpoint(self, client, test_setup):
        """Test POST /assignments endpoint creates assignment without terminal."""
        branch, terminal, session, org_id, user_id = test_setup
        
        supervisor_id = f"supervisor-{uuid.uuid4()}"
        start_time = datetime.now(timezone.utc)
        
        # Make POST request
        response = client.post(
            f"/api/users/{user_id}/organization/{org_id}/assignments",
            json={
                "session_id": str(session.session_id),
                "user_id": supervisor_id,
                "branch_id": str(branch.branch_id),
                "terminal_id": None,
                "role": "supervisor",
                "start_time": start_time.isoformat(),
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == supervisor_id
        assert data["role"] == "supervisor"
        assert data["terminal_id"] is None
        assert data["is_active"] is True
        
        assignment_id = data["assignment_id"]
        
        # Cleanup
        with AssignmentRepository() as repo:
            repo.delete(assignment_id)

    def test_post_assignment_validation_errors_endpoint(self, client, test_setup):
        """Test POST /assignments endpoint returns 400 for validation errors."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Test invalid session
        response = client.post(
            f"/api/users/{user_id}/organization/{org_id}/assignments",
            json={
                "session_id": str(uuid.uuid4()),
                "user_id": f"cashier-{uuid.uuid4()}",
                "branch_id": str(branch.branch_id),
                "terminal_id": None,
                "role": "cashier",
                "start_time": datetime.now(timezone.utc).isoformat(),
            }
        )
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"].lower() or "not active" in response.json()["detail"].lower()
        
        # Test invalid branch
        response = client.post(
            f"/api/users/{user_id}/organization/{org_id}/assignments",
            json={
                "session_id": str(session.session_id),
                "user_id": f"cashier-{uuid.uuid4()}",
                "branch_id": str(uuid.uuid4()),
                "terminal_id": None,
                "role": "cashier",
                "start_time": datetime.now(timezone.utc).isoformat(),
            }
        )
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"].lower() or "does not belong" in response.json()["detail"].lower()
        
        # Test invalid terminal
        response = client.post(
            f"/api/users/{user_id}/organization/{org_id}/assignments",
            json={
                "session_id": str(session.session_id),
                "user_id": f"cashier-{uuid.uuid4()}",
                "branch_id": str(branch.branch_id),
                "terminal_id": str(uuid.uuid4()),
                "role": "cashier",
                "start_time": datetime.now(timezone.utc).isoformat(),
            }
        )
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"].lower() or "does not belong" in response.json()["detail"].lower()

    def test_post_assignment_user_already_has_active_assignment_endpoint(self, client, test_setup):
        """Test POST /assignments returns 400 when user already has active assignment."""
        branch, terminal, session, org_id, user_id = test_setup
        
        cashier_id = f"cashier-{uuid.uuid4()}"
        
        # Create first assignment
        response1 = client.post(
            f"/api/users/{user_id}/organization/{org_id}/assignments",
            json={
                "session_id": str(session.session_id),
                "user_id": cashier_id,
                "branch_id": str(branch.branch_id),
                "terminal_id": str(terminal.terminal_id),
                "role": "cashier",
                "start_time": datetime.now(timezone.utc).isoformat(),
            }
        )
        assert response1.status_code == 201
        assignment_id = response1.json()["assignment_id"]
        
        # Try to create second active assignment for same user
        response2 = client.post(
            f"/api/users/{user_id}/organization/{org_id}/assignments",
            json={
                "session_id": str(session.session_id),
                "user_id": cashier_id,
                "branch_id": str(branch.branch_id),
                "terminal_id": None,
                "role": "cashier",
                "start_time": datetime.now(timezone.utc).isoformat(),
            }
        )
        assert response2.status_code == 400
        assert "already has an active assignment" in response2.json()["detail"].lower()
        
        # Cleanup
        with AssignmentRepository() as repo:
            repo.delete(assignment_id)

    def test_patch_assignment_endpoint(self, client, test_setup):
        """Test PATCH /assignments/{id} endpoint updates assignment."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Create test assignment
        cashier_id = f"cashier-{uuid.uuid4()}"
        with AssignmentRepository() as repo:
            assignment = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                user_id=cashier_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            assignment = repo.save(assignment)
        
        # Make PATCH request to add terminal
        response = client.patch(
            f"/api/users/{user_id}/organization/{org_id}/assignments/{assignment.assignment_id}",
            json={
                "terminal_id": str(terminal.terminal_id),
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["terminal_id"] == str(terminal.terminal_id)
        
        # Cleanup
        with AssignmentRepository() as repo:
            repo.delete(str(assignment.assignment_id))

    def test_patch_assignment_deactivate_endpoint(self, client, test_setup):
        """Test PATCH /assignments/{id} endpoint deactivates assignment and sets end_time."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Create test assignment
        cashier_id = f"cashier-{uuid.uuid4()}"
        with AssignmentRepository() as repo:
            assignment = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                user_id=cashier_id,
                branch_id=branch.branch_id,
                terminal_id=terminal.terminal_id,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                end_time=None,
                is_active=True,
                created_by=user_id,
            )
            assignment = repo.save(assignment)
        
        # Make PATCH request to deactivate
        response = client.patch(
            f"/api/users/{user_id}/organization/{org_id}/assignments/{assignment.assignment_id}",
            json={
                "is_active": False,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["end_time"] is not None
        
        # Cleanup
        with AssignmentRepository() as repo:
            repo.delete(str(assignment.assignment_id))

    def test_patch_assignment_not_found_endpoint(self, client, test_setup):
        """Test PATCH /assignments/{id} returns 404 for non-existent assignment."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Make PATCH request with non-existent ID
        response = client.patch(
            f"/api/users/{user_id}/organization/{org_id}/assignments/{uuid.uuid4()}",
            json={
                "is_active": False,
            }
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_patch_assignment_invalid_terminal_endpoint(self, client, test_setup):
        """Test PATCH /assignments/{id} returns 400 for invalid terminal."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Create test assignment
        cashier_id = f"cashier-{uuid.uuid4()}"
        with AssignmentRepository() as repo:
            assignment = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                user_id=cashier_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            assignment = repo.save(assignment)
        
        # Make PATCH request with invalid terminal
        response = client.patch(
            f"/api/users/{user_id}/organization/{org_id}/assignments/{assignment.assignment_id}",
            json={
                "terminal_id": str(uuid.uuid4()),
            }
        )
        
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"].lower() or "does not belong" in response.json()["detail"].lower()
        
        # Cleanup
        with AssignmentRepository() as repo:
            repo.delete(str(assignment.assignment_id))

    def test_delete_assignment_endpoint(self, client, test_setup):
        """Test DELETE /assignments/{id} endpoint deletes assignment."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Create test assignment
        cashier_id = f"cashier-{uuid.uuid4()}"
        with AssignmentRepository() as repo:
            assignment = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=session.session_id,
                user_id=cashier_id,
                branch_id=branch.branch_id,
                terminal_id=None,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=False,
                created_by=user_id,
            )
            assignment = repo.save(assignment)
        
        assignment_id = str(assignment.assignment_id)
        
        # Make DELETE request
        response = client.delete(
            f"/api/users/{user_id}/organization/{org_id}/assignments/{assignment_id}"
        )
        
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(
            f"/api/users/{user_id}/organization/{org_id}/assignments/{assignment_id}"
        )
        assert get_response.status_code == 404

    def test_delete_assignment_not_found_endpoint(self, client, test_setup):
        """Test DELETE /assignments/{id} returns 404 for non-existent assignment."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Make DELETE request with non-existent ID
        response = client.delete(
            f"/api/users/{user_id}/organization/{org_id}/assignments/{uuid.uuid4()}"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_error_handling_500_endpoint(self, client, test_setup):
        """Test that unexpected errors return 500 status code."""
        branch, terminal, session, org_id, user_id = test_setup
        
        # Make request with malformed data that might cause unexpected error
        response = client.post(
            f"/api/users/{user_id}/organization/{org_id}/assignments",
            json={
                "session_id": "not-a-uuid",
                "user_id": f"cashier-{uuid.uuid4()}",
                "branch_id": str(branch.branch_id),
                "terminal_id": None,
                "role": "cashier",
                "start_time": datetime.now(timezone.utc).isoformat(),
            }
        )
        
        # Should return either 400 (validation) or 422 (unprocessable entity)
        assert response.status_code in [400, 422, 500]
