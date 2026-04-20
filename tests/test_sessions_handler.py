"""
Unit tests for sessions handler (repository, service, controller).
"""
import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.dtos.requests.session_request_dto import (
    SessionCreateRequestDTO,
    SessionUpdateRequestDTO,
)
from app.dtos.responses.session_dto import SessionResponse
from app.models.session import Session
from app.services import session_service


class TestSessionService:
    """Test session service layer."""

    @patch("app.services.session_service.SessionRepository")
    def test_get_sessions_success(self, mock_repo_class):
        """Test getting all sessions for an organization."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        session_id = uuid.uuid4()
        branch_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        mock_session = Session(
            session_id=session_id,
            organization_id=org_id,
            branch_id=branch_id,
            name="Partido vs Herediano",
            type="match",
            context="gradas",
            start_time=now,
            is_active=True,
            expected_revenue=1500000.00,
            created_by=user_id,
        )
        mock_session.created_at = now
        mock_session.updated_at = now

        mock_repo = MagicMock()
        mock_repo.find_all_by_organization.return_value = [mock_session]
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = session_service.get_sessions(org_id, user_id)

        # Assert
        assert len(result) == 1
        assert result[0].session_id == str(session_id)
        assert result[0].name == "Partido vs Herediano"
        assert result[0].type == "match"
        assert result[0].context == "gradas"
        assert result[0].is_active is True
        mock_repo.find_all_by_organization.assert_called_once_with(
            org_id, is_active=None, branch_id=None, session_type=None, context=None
        )

    @patch("app.services.session_service.SessionRepository")
    def test_get_sessions_with_filters(self, mock_repo_class):
        """Test getting sessions with filters."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        branch_id = str(uuid.uuid4())

        mock_repo = MagicMock()
        mock_repo.find_all_by_organization.return_value = []
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = session_service.get_sessions(
            org_id, user_id, is_active=True, branch_id=branch_id, session_type="match", context="gradas"
        )

        # Assert
        mock_repo.find_all_by_organization.assert_called_once_with(
            org_id, is_active=True, branch_id=branch_id, session_type="match", context="gradas"
        )

    @patch("app.services.session_service.SessionRepository")
    def test_create_session_success(self, mock_repo_class):
        """Test creating a new session."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        session_id = uuid.uuid4()
        branch_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        dto = SessionCreateRequestDTO(
            name="Partido vs Herediano",
            type="match",
            context="gradas",
            branch_id=branch_id,
            start_time=now,
            expected_revenue=1500000.00,
        )

        mock_session = Session(
            session_id=session_id,
            organization_id=org_id,
            branch_id=uuid.UUID(branch_id),
            name=dto.name,
            type=dto.type,
            context=dto.context,
            start_time=dto.start_time,
            is_active=True,
            expected_revenue=dto.expected_revenue,
            created_by=user_id,
        )
        mock_session.created_at = now
        mock_session.updated_at = now

        mock_repo = MagicMock()
        mock_repo.validate_branch_exists.return_value = True
        mock_repo.save.return_value = mock_session
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = session_service.create_session(org_id, user_id, dto)

        # Assert
        assert result.name == "Partido vs Herediano"
        assert result.type == "match"
        assert result.context == "gradas"
        assert result.is_active is True
        assert result.expected_revenue == 1500000.00
        mock_repo.validate_branch_exists.assert_called_once_with(branch_id, org_id)
        mock_repo.save.assert_called_once()

    @patch("app.services.session_service.SessionRepository")
    def test_create_session_without_branch(self, mock_repo_class):
        """Test creating a session without a branch."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        session_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        dto = SessionCreateRequestDTO(
            name="Turno Mañana",
            type="shift",
            context="caja",
            start_time=now,
        )

        mock_session = Session(
            session_id=session_id,
            organization_id=org_id,
            branch_id=None,
            name=dto.name,
            type=dto.type,
            context=dto.context,
            start_time=dto.start_time,
            is_active=True,
            created_by=user_id,
        )
        mock_session.created_at = now
        mock_session.updated_at = now

        mock_repo = MagicMock()
        mock_repo.save.return_value = mock_session
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = session_service.create_session(org_id, user_id, dto)

        # Assert
        assert result.name == "Turno Mañana"
        assert result.branch_id is None
        mock_repo.validate_branch_exists.assert_not_called()
        mock_repo.save.assert_called_once()

    @patch("app.services.session_service.SessionRepository")
    def test_create_session_invalid_branch(self, mock_repo_class):
        """Test creating a session with invalid branch fails."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        branch_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        dto = SessionCreateRequestDTO(
            name="Partido vs Herediano",
            type="match",
            context="gradas",
            branch_id=branch_id,
            start_time=now,
        )

        mock_repo = MagicMock()
        mock_repo.validate_branch_exists.return_value = False
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act & Assert
        with pytest.raises(ValueError, match="does not exist"):
            session_service.create_session(org_id, user_id, dto)

    @patch("app.services.session_service.SessionRepository")
    def test_update_session_success(self, mock_repo_class):
        """Test updating a session."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        session_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        existing_session = Session(
            session_id=session_id,
            organization_id=org_id,
            branch_id=None,
            name="Partido vs Herediano",
            type="match",
            context="gradas",
            start_time=now,
            is_active=True,
            created_by=user_id,
        )
        existing_session.created_at = now
        existing_session.updated_at = now

        dto = SessionUpdateRequestDTO(
            name="Partido vs Herediano - Final",
            actual_revenue=1800000.00,
        )

        mock_repo = MagicMock()
        mock_repo.find_by_id_and_organization.return_value = existing_session
        mock_repo.save.return_value = existing_session
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = session_service.update_session(org_id, user_id, str(session_id), dto)

        # Assert
        assert result is not None
        assert result.name == "Partido vs Herediano - Final"
        assert result.actual_revenue == 1800000.00
        mock_repo.save.assert_called_once()

    @patch("app.services.session_service.SessionRepository")
    def test_update_session_deactivate_sets_end_time(self, mock_repo_class):
        """Test deactivating a session automatically sets end_time."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        session_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        existing_session = Session(
            session_id=session_id,
            organization_id=org_id,
            branch_id=None,
            name="Partido vs Herediano",
            type="match",
            context="gradas",
            start_time=now,
            end_time=None,
            is_active=True,
            created_by=user_id,
        )
        existing_session.created_at = now
        existing_session.updated_at = now

        dto = SessionUpdateRequestDTO(
            is_active=False,
        )

        mock_repo = MagicMock()
        mock_repo.find_by_id_and_organization.return_value = existing_session
        mock_repo.save.return_value = existing_session
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = session_service.update_session(org_id, user_id, str(session_id), dto)

        # Assert
        assert result is not None
        assert result.is_active is False
        assert existing_session.end_time is not None
        mock_repo.save.assert_called_once()

    @patch("app.services.session_service.SessionRepository")
    def test_delete_session_with_active_assignments(self, mock_repo_class):
        """Test deleting a session with active assignments fails."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        session_id = uuid.uuid4()

        existing_session = Session(
            session_id=session_id,
            organization_id=org_id,
            branch_id=None,
            name="Partido vs Herediano",
            type="match",
            context="gradas",
            start_time=datetime.now(timezone.utc),
            is_active=True,
            created_by=user_id,
        )

        mock_repo = MagicMock()
        mock_repo.find_by_id_and_organization.return_value = existing_session
        mock_repo.has_active_assignments.return_value = True
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act & Assert
        with pytest.raises(ValueError, match="active assignments"):
            session_service.delete_session(org_id, user_id, str(session_id))

    @patch("app.services.session_service.SessionRepository")
    def test_delete_session_success(self, mock_repo_class):
        """Test deleting a session successfully."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        session_id = uuid.uuid4()

        existing_session = Session(
            session_id=session_id,
            organization_id=org_id,
            branch_id=None,
            name="Partido vs Herediano",
            type="match",
            context="gradas",
            start_time=datetime.now(timezone.utc),
            is_active=False,
            created_by=user_id,
        )

        mock_repo = MagicMock()
        mock_repo.find_by_id_and_organization.return_value = existing_session
        mock_repo.has_active_assignments.return_value = False
        mock_repo.delete.return_value = True
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = session_service.delete_session(org_id, user_id, str(session_id))

        # Assert
        assert result is True
        mock_repo.delete.assert_called_once_with(str(session_id))

    @patch("app.services.session_service.SessionRepository")
    def test_get_session_not_found(self, mock_repo_class):
        """Test getting a non-existent session returns None."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        session_id = str(uuid.uuid4())

        mock_repo = MagicMock()
        mock_repo.find_by_id_and_organization.return_value = None
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = session_service.get_session(org_id, user_id, session_id)

        # Assert
        assert result is None
