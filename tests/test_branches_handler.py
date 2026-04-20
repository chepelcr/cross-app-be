"""
Unit tests for branches handler (repository, service, controller).
"""
import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.dtos.requests.branch_request_dto import (
    BranchCreateRequestDTO,
    BranchUpdateRequestDTO,
)
from app.dtos.responses.branch_dto import BranchResponse
from app.models.branch import Branch
from app.services import branch_service


class TestBranchService:
    """Test branch service layer."""

    @patch("app.services.branch_service.BranchRepository")
    def test_get_branches_success(self, mock_repo_class):
        """Test getting all branches for an organization."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        branch_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        mock_branch = Branch(
            branch_id=branch_id,
            organization_id=org_id,
            name="Puesto 1",
            code="P1",
            type="stand",
            is_active=True,
            address="Estadio Lito Pérez",
            phone="1234-5678",
            created_by=user_id,
        )
        mock_branch.created_at = now
        mock_branch.updated_at = now

        mock_repo = MagicMock()
        mock_repo.find_all_by_organization.return_value = [mock_branch]
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = branch_service.get_branches(org_id, user_id)

        # Assert
        assert len(result) == 1
        assert result[0].branch_id == str(branch_id)
        assert result[0].name == "Puesto 1"
        assert result[0].code == "P1"
        assert result[0].type == "stand"
        mock_repo.find_all_by_organization.assert_called_once_with(
            org_id, is_active=None, branch_type=None
        )

    @patch("app.services.branch_service.BranchRepository")
    def test_create_branch_success(self, mock_repo_class):
        """Test creating a new branch."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        branch_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        dto = BranchCreateRequestDTO(
            name="Puesto 1",
            code="P1",
            type="stand",
            address="Estadio Lito Pérez",
            phone="1234-5678",
        )

        mock_branch = Branch(
            branch_id=branch_id,
            organization_id=org_id,
            name=dto.name,
            code=dto.code,
            type=dto.type,
            is_active=True,
            address=dto.address,
            phone=dto.phone,
            created_by=user_id,
        )
        mock_branch.created_at = now
        mock_branch.updated_at = now

        mock_repo = MagicMock()
        mock_repo.find_by_code_and_organization.return_value = None
        mock_repo.save.return_value = mock_branch
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = branch_service.create_branch(org_id, user_id, dto)

        # Assert
        assert result.name == "Puesto 1"
        assert result.code == "P1"
        assert result.type == "stand"
        assert result.is_active is True
        mock_repo.find_by_code_and_organization.assert_called_once_with("P1", org_id)
        mock_repo.save.assert_called_once()

    @patch("app.services.branch_service.BranchRepository")
    def test_create_branch_duplicate_code(self, mock_repo_class):
        """Test creating a branch with duplicate code fails."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"

        dto = BranchCreateRequestDTO(
            name="Puesto 1",
            code="P1",
            type="stand",
        )

        existing_branch = Branch(
            branch_id=uuid.uuid4(),
            organization_id=org_id,
            name="Existing Branch",
            code="P1",
            type="stand",
            is_active=True,
            created_by=user_id,
        )

        mock_repo = MagicMock()
        mock_repo.find_by_code_and_organization.return_value = existing_branch
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            branch_service.create_branch(org_id, user_id, dto)

    @patch("app.services.branch_service.BranchRepository")
    def test_update_branch_success(self, mock_repo_class):
        """Test updating a branch."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        branch_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        existing_branch = Branch(
            branch_id=branch_id,
            organization_id=org_id,
            name="Puesto 1",
            code="P1",
            type="stand",
            is_active=True,
            created_by=user_id,
        )
        existing_branch.created_at = now
        existing_branch.updated_at = now

        dto = BranchUpdateRequestDTO(
            name="Puesto 1 - Actualizado",
            is_active=False,
        )

        mock_repo = MagicMock()
        mock_repo.find_by_id_and_organization.return_value = existing_branch
        mock_repo.save.return_value = existing_branch
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = branch_service.update_branch(org_id, user_id, str(branch_id), dto)

        # Assert
        assert result is not None
        assert result.name == "Puesto 1 - Actualizado"
        assert result.is_active is False
        mock_repo.save.assert_called_once()

    @patch("app.services.branch_service.BranchRepository")
    def test_delete_branch_with_active_terminals(self, mock_repo_class):
        """Test deleting a branch with active terminals fails."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        branch_id = uuid.uuid4()

        existing_branch = Branch(
            branch_id=branch_id,
            organization_id=org_id,
            name="Puesto 1",
            code="P1",
            type="stand",
            is_active=True,
            created_by=user_id,
        )

        mock_repo = MagicMock()
        mock_repo.find_by_id_and_organization.return_value = existing_branch
        mock_repo.has_active_terminals.return_value = True
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act & Assert
        with pytest.raises(ValueError, match="active terminals"):
            branch_service.delete_branch(org_id, user_id, str(branch_id))

    @patch("app.services.branch_service.BranchRepository")
    def test_delete_branch_with_active_sessions(self, mock_repo_class):
        """Test deleting a branch with active sessions fails."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        branch_id = uuid.uuid4()

        existing_branch = Branch(
            branch_id=branch_id,
            organization_id=org_id,
            name="Puesto 1",
            code="P1",
            type="stand",
            is_active=True,
            created_by=user_id,
        )

        mock_repo = MagicMock()
        mock_repo.find_by_id_and_organization.return_value = existing_branch
        mock_repo.has_active_terminals.return_value = False
        mock_repo.has_active_sessions.return_value = True
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act & Assert
        with pytest.raises(ValueError, match="active sessions"):
            branch_service.delete_branch(org_id, user_id, str(branch_id))

    @patch("app.services.branch_service.BranchRepository")
    def test_delete_branch_success(self, mock_repo_class):
        """Test deleting a branch successfully."""
        # Arrange
        org_id = "org-123"
        user_id = "user-456"
        branch_id = uuid.uuid4()

        existing_branch = Branch(
            branch_id=branch_id,
            organization_id=org_id,
            name="Puesto 1",
            code="P1",
            type="stand",
            is_active=True,
            created_by=user_id,
        )

        mock_repo = MagicMock()
        mock_repo.find_by_id_and_organization.return_value = existing_branch
        mock_repo.has_active_terminals.return_value = False
        mock_repo.has_active_sessions.return_value = False
        mock_repo.delete.return_value = True
        mock_repo_class.return_value.__enter__.return_value = mock_repo

        # Act
        result = branch_service.delete_branch(org_id, user_id, str(branch_id))

        # Assert
        assert result is True
        mock_repo.delete.assert_called_once_with(str(branch_id))
