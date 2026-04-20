"""
Integration tests for sessions handler with real database operations.
"""
import pytest
import uuid
from datetime import datetime, timezone, timedelta

from app.models.session import Session
from app.models.branch import Branch
from app.repositories.session_repository import SessionRepository
from app.repositories.branch_repository import BranchRepository
from app.services import session_service
from app.dtos.requests.session_request_dto import (
    SessionCreateRequestDTO,
    SessionUpdateRequestDTO,
)


@pytest.mark.integration
class TestSessionIntegration:
    """Integration tests for session operations with database."""

    @pytest.fixture
    def test_branch(self):
        """Create a test branch for session tests."""
        org_id = f"test-org-{uuid.uuid4()}"
        user_id = f"test-user-{uuid.uuid4()}"
        
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
            
        yield branch, org_id, user_id
        
        # Cleanup
        with BranchRepository() as repo:
            repo.delete(str(branch.branch_id))

    def test_create_and_retrieve_session(self, test_branch):
        """Test creating a session and retrieving it."""
        branch, org_id, user_id = test_branch
        
        # Create session
        start_time = datetime.now(timezone.utc)
        dto = SessionCreateRequestDTO(
            name="Partido vs Herediano",
            type="match",
            context="gradas",
            branch_id=str(branch.branch_id),
            start_time=start_time,
            expected_revenue=1500000.00,
        )
        
        created = session_service.create_session(org_id, user_id, dto)
        
        assert created is not None
        assert created.name == "Partido vs Herediano"
        assert created.type == "match"
        assert created.context == "gradas"
        assert created.branch_id == str(branch.branch_id)
        assert created.is_active is True
        assert created.expected_revenue == 1500000.00
        
        # Retrieve session
        retrieved = session_service.get_session(org_id, user_id, created.session_id)
        
        assert retrieved is not None
        assert retrieved.session_id == created.session_id
        assert retrieved.name == created.name
        
        # Cleanup
        with SessionRepository() as repo:
            repo.delete(created.session_id)

    def test_create_session_without_branch(self, test_branch):
        """Test creating a session without a branch."""
        _, org_id, user_id = test_branch
        
        # Create session without branch
        start_time = datetime.now(timezone.utc)
        dto = SessionCreateRequestDTO(
            name="Turno Mañana",
            type="shift",
            context="caja",
            start_time=start_time,
        )
        
        created = session_service.create_session(org_id, user_id, dto)
        
        assert created is not None
        assert created.name == "Turno Mañana"
        assert created.branch_id is None
        assert created.is_active is True
        
        # Cleanup
        with SessionRepository() as repo:
            repo.delete(created.session_id)

    def test_update_session(self, test_branch):
        """Test updating a session."""
        branch, org_id, user_id = test_branch
        
        # Create session
        with SessionRepository() as repo:
            session = Session(
                session_id=uuid.uuid4(),
                organization_id=org_id,
                branch_id=branch.branch_id,
                name="Original Name",
                type="match",
                context="gradas",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            session = repo.save(session)
        
        # Update session
        dto = SessionUpdateRequestDTO(
            name="Updated Name",
            actual_revenue=1800000.00,
        )
        
        updated = session_service.update_session(
            org_id, user_id, str(session.session_id), dto
        )
        
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.actual_revenue == 1800000.00
        
        # Cleanup
        with SessionRepository() as repo:
            repo.delete(str(session.session_id))

    def test_deactivate_session_sets_end_time(self, test_branch):
        """Test that deactivating a session automatically sets end_time."""
        branch, org_id, user_id = test_branch
        
        # Create session
        with SessionRepository() as repo:
            session = Session(
                session_id=uuid.uuid4(),
                organization_id=org_id,
                branch_id=branch.branch_id,
                name="Active Session",
                type="match",
                context="gradas",
                start_time=datetime.now(timezone.utc),
                end_time=None,
                is_active=True,
                created_by=user_id,
            )
            session = repo.save(session)
        
        session_id = str(session.session_id)
        
        # Deactivate session
        dto = SessionUpdateRequestDTO(
            is_active=False,
        )
        
        updated = session_service.update_session(org_id, user_id, session_id, dto)
        
        assert updated is not None
        assert updated.is_active is False
        assert updated.end_time is not None
        
        # Cleanup
        with SessionRepository() as repo:
            repo.delete(session_id)

    def test_delete_session(self, test_branch):
        """Test deleting a session."""
        branch, org_id, user_id = test_branch
        
        # Create session
        with SessionRepository() as repo:
            session = Session(
                session_id=uuid.uuid4(),
                organization_id=org_id,
                branch_id=branch.branch_id,
                name="Session to Delete",
                type="shift",
                context="caja",
                start_time=datetime.now(timezone.utc),
                is_active=False,
                created_by=user_id,
            )
            session = repo.save(session)
        
        session_id = str(session.session_id)
        
        # Delete session
        result = session_service.delete_session(org_id, user_id, session_id)
        
        assert result is True
        
        # Verify deletion
        retrieved = session_service.get_session(org_id, user_id, session_id)
        assert retrieved is None

    def test_list_sessions_with_filters(self, test_branch):
        """Test listing sessions with filters."""
        branch, org_id, user_id = test_branch
        
        # Create multiple sessions
        sessions = []
        with SessionRepository() as repo:
            for i in range(4):
                session = Session(
                    session_id=uuid.uuid4(),
                    organization_id=org_id,
                    branch_id=branch.branch_id if i < 2 else None,
                    name=f"Session {i}",
                    type="match" if i % 2 == 0 else "shift",
                    context="gradas" if i < 2 else "caja",
                    start_time=datetime.now(timezone.utc) - timedelta(hours=i),
                    is_active=(i % 2 == 0),
                    created_by=user_id,
                )
                session = repo.save(session)
                sessions.append(session)
        
        # Test filter by is_active
        active_sessions = session_service.get_sessions(
            org_id, user_id, is_active=True
        )
        assert len(active_sessions) >= 2
        
        # Test filter by branch_id
        branch_sessions = session_service.get_sessions(
            org_id, user_id, branch_id=str(branch.branch_id)
        )
        assert len(branch_sessions) >= 2
        
        # Test filter by type
        match_sessions = session_service.get_sessions(
            org_id, user_id, session_type="match"
        )
        assert len(match_sessions) >= 2
        
        # Test filter by context
        gradas_sessions = session_service.get_sessions(
            org_id, user_id, context="gradas"
        )
        assert len(gradas_sessions) >= 2
        
        # Test multiple filters
        filtered_sessions = session_service.get_sessions(
            org_id, user_id, is_active=True, session_type="match"
        )
        assert len(filtered_sessions) >= 1
        
        # Cleanup
        with SessionRepository() as repo:
            for session in sessions:
                repo.delete(str(session.session_id))

    def test_branch_validation(self, test_branch):
        """Test that session creation validates branch existence."""
        _, org_id, user_id = test_branch
        
        # Try to create session with non-existent branch
        dto = SessionCreateRequestDTO(
            name="Invalid Session",
            type="match",
            context="gradas",
            branch_id=str(uuid.uuid4()),
            start_time=datetime.now(timezone.utc),
        )
        
        with pytest.raises(ValueError, match="does not exist or does not belong"):
            session_service.create_session(org_id, user_id, dto)

    def test_session_type_validation(self, test_branch):
        """Test that session type is validated."""
        branch, org_id, user_id = test_branch
        
        # Try to create session with invalid type
        with pytest.raises(ValueError, match="Type must be one of"):
            dto = SessionCreateRequestDTO(
                name="Invalid Type Session",
                type="invalid_type",
                context="gradas",
                branch_id=str(branch.branch_id),
                start_time=datetime.now(timezone.utc),
            )

    def test_session_context_validation(self, test_branch):
        """Test that session context is validated."""
        branch, org_id, user_id = test_branch
        
        # Try to create session with invalid context
        with pytest.raises(ValueError, match="Context must be one of"):
            dto = SessionCreateRequestDTO(
                name="Invalid Context Session",
                type="match",
                context="invalid_context",
                branch_id=str(branch.branch_id),
                start_time=datetime.now(timezone.utc),
            )

    def test_organization_scoped_data_isolation(self, test_branch):
        """Test that sessions are isolated by organization."""
        branch, org_id, user_id = test_branch
        other_org_id = f"test-org-{uuid.uuid4()}"
        
        # Create session in first organization
        with SessionRepository() as repo:
            session = Session(
                session_id=uuid.uuid4(),
                organization_id=org_id,
                branch_id=branch.branch_id,
                name="Org 1 Session",
                type="match",
                context="gradas",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            session = repo.save(session)
        
        session_id = str(session.session_id)
        
        # Try to retrieve from different organization
        retrieved = session_service.get_session(other_org_id, user_id, session_id)
        assert retrieved is None
        
        # Verify it exists in correct organization
        retrieved = session_service.get_session(org_id, user_id, session_id)
        assert retrieved is not None
        
        # Cleanup
        with SessionRepository() as repo:
            repo.delete(session_id)

    def test_sessions_ordered_by_start_time_desc(self, test_branch):
        """Test that sessions are returned ordered by start_time descending."""
        branch, org_id, user_id = test_branch
        
        # Create sessions with different start times
        sessions = []
        with SessionRepository() as repo:
            for i in range(3):
                session = Session(
                    session_id=uuid.uuid4(),
                    organization_id=org_id,
                    branch_id=branch.branch_id,
                    name=f"Session {i}",
                    type="match",
                    context="gradas",
                    start_time=datetime.now(timezone.utc) - timedelta(hours=i),
                    is_active=True,
                    created_by=user_id,
                )
                session = repo.save(session)
                sessions.append(session)
        
        # Get all sessions
        retrieved = session_service.get_sessions(org_id, user_id)
        
        # Verify ordering (most recent first)
        session_ids = [s.session_id for s in retrieved]
        our_session_ids = [str(s.session_id) for s in sessions]
        
        # Find positions of our sessions in the result
        positions = [session_ids.index(sid) for sid in our_session_ids if sid in session_ids]
        
        # Verify they are in descending order (Session 0 should come before Session 1, etc.)
        assert positions == sorted(positions)
        
        # Cleanup
        with SessionRepository() as repo:
            for session in sessions:
                repo.delete(str(session.session_id))
