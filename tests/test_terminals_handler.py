"""
Unit tests for terminals handler (repository, service, controller).
"""
import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.dtos.requests.terminal_request_dto import (
    TerminalCreateRequestDTO,
    TerminalUpdateRequestDTO,
)
from app.dtos.responses.terminal_dto import TerminalResponse
from app.models.terminal import Terminal
from app.services import terminal_service


class TestTerminalService:
    """Test terminal service layer."""

    @patch("app.services.terminal_service.TerminalRepository")
    def test_get_terminals_success(self, mock_repo_class):
        """Test getting all terminals for an organization."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        terminal_id = uuid.uuid4()
        branch_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        mock_terminal = Terminal(
            terminal_id=terminal_id,
            organization_id=org_id,
            branch_id=branch_id,
            name="Terminal 1",
            code="T1",
            device_id="device-123",
            is_active=True,
            registered_at=now,
        )
        mock_terminal.created_at = now
        mock_terminal.updated_at = now

        mock_repo = MagicMock()
        mock_repo.find_all_by_organization.return_value = [mock_terminal]
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = terminal_service.get_terminals(org_id, user_id)

        # Assert
        assert len(result) == 1
        assert result[0].terminal_id == str(terminal_id)
        assert result[0].name == "Terminal 1"
        assert result[0].code == "T1"
        assert result[0].device_id == "device-123"
        mock_repo.find_all_by_organization.assert_called_once_with(
            org_id, is_active=None, branch_id=None
        )

    @patch("app.services.terminal_service.TerminalRepository")
    def test_create_terminal_success(self, mock_repo_class):
        """Test creating a new terminal."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        terminal_id = uuid.uuid4()
        branch_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        dto = TerminalCreateRequestDTO(
            branch_id=str(branch_id),
            name="Terminal 1",
            code="T1",
            device_id="device-123",
        )

        mock_terminal = Terminal(
            terminal_id=terminal_id,
            organization_id=org_id,
            branch_id=branch_id,
            name=dto.name,
            code=dto.code,
            device_id=dto.device_id,
            is_active=True,
            registered_at=now,
        )
        mock_terminal.created_at = now
        mock_terminal.updated_at = now

        mock_repo = MagicMock()
        mock_repo.validate_branch_exists.return_value = True
        mock_repo.find_by_code_and_organization.return_value = None
        mock_repo.find_by_device_id.return_value = None
        mock_repo.save.return_value = mock_terminal
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = terminal_service.create_terminal(org_id, user_id, dto)

        # Assert
        assert result.name == "Terminal 1"
        assert result.code == "T1"
        assert result.device_id == "device-123"
        assert result.is_active is True
        mock_repo.validate_branch_exists.assert_called_once_with(str(branch_id), org_id)
        mock_repo.find_by_code_and_organization.assert_called_once_with("T1", org_id)
        mock_repo.find_by_device_id.assert_called_once_with("device-123")
        mock_repo.save.assert_called_once()

    @patch("app.services.terminal_service.TerminalRepository")
    def test_create_terminal_invalid_branch(self, mock_repo_class):
        """Test creating a terminal with invalid branch fails."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        branch_id = uuid.uuid4()

        dto = TerminalCreateRequestDTO(
            branch_id=str(branch_id),
            name="Terminal 1",
            code="T1",
        )

        mock_repo = MagicMock()
        mock_repo.validate_branch_exists.return_value = False
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act & Assert
        with pytest.raises(ValueError, match="does not exist or does not belong"):
            terminal_service.create_terminal(org_id, user_id, dto)

    @patch("app.services.terminal_service.TerminalRepository")
    def test_create_terminal_duplicate_code(self, mock_repo_class):
        """Test creating a terminal with duplicate code fails."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        branch_id = uuid.uuid4()

        dto = TerminalCreateRequestDTO(
            branch_id=str(branch_id),
            name="Terminal 1",
            code="T1",
        )

        existing_terminal = Terminal(
            terminal_id=uuid.uuid4(),
            organization_id=org_id,
            branch_id=branch_id,
            name="Existing Terminal",
            code="T1",
            is_active=True,
            registered_at=datetime.now(timezone.utc),
        )

        mock_repo = MagicMock()
        mock_repo.validate_branch_exists.return_value = True
        mock_repo.find_by_code_and_organization.return_value = existing_terminal
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            terminal_service.create_terminal(org_id, user_id, dto)

    @patch("app.services.terminal_service.TerminalRepository")
    def test_create_terminal_duplicate_device_id(self, mock_repo_class):
        """Test creating a terminal with duplicate device_id fails."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        branch_id = uuid.uuid4()

        dto = TerminalCreateRequestDTO(
            branch_id=str(branch_id),
            name="Terminal 1",
            code="T1",
            device_id="device-123",
        )

        existing_terminal = Terminal(
            terminal_id=uuid.uuid4(),
            organization_id=org_id,
            branch_id=branch_id,
            name="Existing Terminal",
            code="T2",
            device_id="device-123",
            is_active=True,
            registered_at=datetime.now(timezone.utc),
        )

        mock_repo = MagicMock()
        mock_repo.validate_branch_exists.return_value = True
        mock_repo.find_by_code_and_organization.return_value = None
        mock_repo.find_by_device_id.return_value = existing_terminal
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act & Assert
        with pytest.raises(ValueError, match="already registered"):
            terminal_service.create_terminal(org_id, user_id, dto)

    @patch("app.services.terminal_service.TerminalRepository")
    def test_update_terminal_success(self, mock_repo_class):
        """Test updating a terminal."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        terminal_id = uuid.uuid4()
        branch_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        existing_terminal = Terminal(
            terminal_id=terminal_id,
            organization_id=org_id,
            branch_id=branch_id,
            name="Terminal 1",
            code="T1",
            is_active=True,
            registered_at=now,
        )
        existing_terminal.created_at = now
        existing_terminal.updated_at = now

        dto = TerminalUpdateRequestDTO(
            name="Terminal 1 - Actualizado",
            is_active=False,
        )

        mock_repo = MagicMock()
        mock_repo.find_by_id_and_organization.return_value = existing_terminal
        mock_repo.save.return_value = existing_terminal
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = terminal_service.update_terminal(org_id, user_id, str(terminal_id), dto)

        # Assert
        assert result is not None
        assert result.name == "Terminal 1 - Actualizado"
        assert result.is_active is False
        mock_repo.save.assert_called_once()

    @patch("app.services.terminal_service.TerminalRepository")
    def test_update_terminal_change_branch(self, mock_repo_class):
        """Test updating a terminal's branch."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        terminal_id = uuid.uuid4()
        old_branch_id = uuid.uuid4()
        new_branch_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        existing_terminal = Terminal(
            terminal_id=terminal_id,
            organization_id=org_id,
            branch_id=old_branch_id,
            name="Terminal 1",
            code="T1",
            is_active=True,
            registered_at=now,
        )
        existing_terminal.created_at = now
        existing_terminal.updated_at = now

        dto = TerminalUpdateRequestDTO(
            branch_id=str(new_branch_id),
        )

        mock_repo = MagicMock()
        mock_repo.find_by_id_and_organization.return_value = existing_terminal
        mock_repo.validate_branch_exists.return_value = True
        mock_repo.save.return_value = existing_terminal
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = terminal_service.update_terminal(org_id, user_id, str(terminal_id), dto)

        # Assert
        assert result is not None
        mock_repo.validate_branch_exists.assert_called_once_with(str(new_branch_id), org_id)
        mock_repo.save.assert_called_once()

    @patch("app.services.terminal_service.TerminalRepository")
    def test_delete_terminal_with_active_assignments(self, mock_repo_class):
        """Test deleting a terminal with active assignments fails."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        terminal_id = uuid.uuid4()
        branch_id = uuid.uuid4()

        existing_terminal = Terminal(
            terminal_id=terminal_id,
            organization_id=org_id,
            branch_id=branch_id,
            name="Terminal 1",
            code="T1",
            is_active=True,
            registered_at=datetime.now(timezone.utc),
        )

        mock_repo = MagicMock()
        mock_repo.find_by_id_and_organization.return_value = existing_terminal
        mock_repo.has_active_assignments.return_value = True
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act & Assert
        with pytest.raises(ValueError, match="active assignments"):
            terminal_service.delete_terminal(org_id, user_id, str(terminal_id))

    @patch("app.services.terminal_service.TerminalRepository")
    def test_delete_terminal_success(self, mock_repo_class):
        """Test deleting a terminal successfully."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        terminal_id = uuid.uuid4()
        branch_id = uuid.uuid4()

        existing_terminal = Terminal(
            terminal_id=terminal_id,
            organization_id=org_id,
            branch_id=branch_id,
            name="Terminal 1",
            code="T1",
            is_active=True,
            registered_at=datetime.now(timezone.utc),
        )

        mock_repo = MagicMock()
        mock_repo.find_by_id_and_organization.return_value = existing_terminal
        mock_repo.has_active_assignments.return_value = False
        mock_repo.delete.return_value = True
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = terminal_service.delete_terminal(org_id, user_id, str(terminal_id))

        # Assert
        assert result is True
        mock_repo.delete.assert_called_once_with(str(terminal_id))

    @patch("app.services.terminal_service.TerminalRepository")
    def test_get_terminals_with_filters(self, mock_repo_class):
        """Test getting terminals with filters."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        branch_id = str(uuid.uuid4())

        mock_repo = MagicMock()
        mock_repo.find_all_by_organization.return_value = []
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = terminal_service.get_terminals(
            org_id, user_id, is_active=True, branch_id=branch_id
        )

        # Assert
        mock_repo.find_all_by_organization.assert_called_once_with(
            org_id, is_active=True, branch_id=branch_id
        )
