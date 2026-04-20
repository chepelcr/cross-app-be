"""
Integration tests for terminals handler with real database operations.
"""
import pytest
import uuid
from datetime import datetime, timezone

from app.models.terminal import Terminal
from app.models.branch import Branch
from app.repositories.terminal_repository import TerminalRepository
from app.repositories.branch_repository import BranchRepository
from app.services import terminal_service
from app.dtos.requests.terminal_request_dto import (
    TerminalCreateRequestDTO,
    TerminalUpdateRequestDTO,
)


@pytest.mark.integration
class TestTerminalIntegration:
    """Integration tests for terminal operations with database."""

    @pytest.fixture
    def test_branch(self):
        """Create a test branch for terminal tests."""
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

    def test_create_and_retrieve_terminal(self, test_branch):
        """Test creating a terminal and retrieving it."""
        branch, org_id, user_id = test_branch
        
        # Create terminal
        dto = TerminalCreateRequestDTO(
            branch_id=str(branch.branch_id),
            name="Test Terminal",
            code=f"TT-{uuid.uuid4().hex[:6]}",
            device_id=f"device-{uuid.uuid4().hex[:8]}",
        )
        
        created = terminal_service.create_terminal(org_id, user_id, dto)
        
        assert created is not None
        assert created.name == "Test Terminal"
        assert created.code == dto.code
        assert created.device_id == dto.device_id
        assert created.branch_id == str(branch.branch_id)
        assert created.is_active is True
        
        # Retrieve terminal
        retrieved = terminal_service.get_terminal(org_id, user_id, created.terminal_id)
        
        assert retrieved is not None
        assert retrieved.terminal_id == created.terminal_id
        assert retrieved.name == created.name
        
        # Cleanup
        with TerminalRepository() as repo:
            repo.delete(created.terminal_id)

    def test_update_terminal(self, test_branch):
        """Test updating a terminal."""
        branch, org_id, user_id = test_branch
        
        # Create terminal
        with TerminalRepository() as repo:
            terminal = Terminal(
                terminal_id=uuid.uuid4(),
                organization_id=org_id,
                branch_id=branch.branch_id,
                name="Original Name",
                code=f"TT-{uuid.uuid4().hex[:6]}",
                is_active=True,
                registered_at=datetime.now(timezone.utc),
            )
            terminal = repo.save(terminal)
        
        # Update terminal
        dto = TerminalUpdateRequestDTO(
            name="Updated Name",
            is_active=False,
        )
        
        updated = terminal_service.update_terminal(
            org_id, user_id, str(terminal.terminal_id), dto
        )
        
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.is_active is False
        
        # Cleanup
        with TerminalRepository() as repo:
            repo.delete(str(terminal.terminal_id))

    def test_delete_terminal(self, test_branch):
        """Test deleting a terminal."""
        branch, org_id, user_id = test_branch
        
        # Create terminal
        with TerminalRepository() as repo:
            terminal = Terminal(
                terminal_id=uuid.uuid4(),
                organization_id=org_id,
                branch_id=branch.branch_id,
                name="Terminal to Delete",
                code=f"TT-{uuid.uuid4().hex[:6]}",
                is_active=True,
                registered_at=datetime.now(timezone.utc),
            )
            terminal = repo.save(terminal)
        
        terminal_id = str(terminal.terminal_id)
        
        # Delete terminal
        result = terminal_service.delete_terminal(org_id, user_id, terminal_id)
        
        assert result is True
        
        # Verify deletion
        retrieved = terminal_service.get_terminal(org_id, user_id, terminal_id)
        assert retrieved is None

    def test_list_terminals_with_filters(self, test_branch):
        """Test listing terminals with filters."""
        branch, org_id, user_id = test_branch
        
        # Create multiple terminals
        terminals = []
        with TerminalRepository() as repo:
            for i in range(3):
                terminal = Terminal(
                    terminal_id=uuid.uuid4(),
                    organization_id=org_id,
                    branch_id=branch.branch_id,
                    name=f"Terminal {i}",
                    code=f"TT-{uuid.uuid4().hex[:6]}",
                    is_active=(i % 2 == 0),  # Alternate active/inactive
                    registered_at=datetime.now(timezone.utc),
                )
                terminal = repo.save(terminal)
                terminals.append(terminal)
        
        # Test filter by is_active
        active_terminals = terminal_service.get_terminals(
            org_id, user_id, is_active=True
        )
        assert len(active_terminals) >= 2  # At least our 2 active terminals
        
        # Test filter by branch_id
        branch_terminals = terminal_service.get_terminals(
            org_id, user_id, branch_id=str(branch.branch_id)
        )
        assert len(branch_terminals) >= 3  # At least our 3 terminals
        
        # Cleanup
        with TerminalRepository() as repo:
            for terminal in terminals:
                repo.delete(str(terminal.terminal_id))

    def test_code_uniqueness_within_organization(self, test_branch):
        """Test that terminal codes must be unique within an organization."""
        branch, org_id, user_id = test_branch
        
        code = f"TT-{uuid.uuid4().hex[:6]}"
        
        # Create first terminal
        dto1 = TerminalCreateRequestDTO(
            branch_id=str(branch.branch_id),
            name="Terminal 1",
            code=code,
        )
        
        created1 = terminal_service.create_terminal(org_id, user_id, dto1)
        
        # Try to create second terminal with same code
        dto2 = TerminalCreateRequestDTO(
            branch_id=str(branch.branch_id),
            name="Terminal 2",
            code=code,
        )
        
        with pytest.raises(ValueError, match="already exists"):
            terminal_service.create_terminal(org_id, user_id, dto2)
        
        # Cleanup
        with TerminalRepository() as repo:
            repo.delete(created1.terminal_id)

    def test_device_id_global_uniqueness(self, test_branch):
        """Test that device_id must be globally unique."""
        branch, org_id, user_id = test_branch
        
        device_id = f"device-{uuid.uuid4().hex[:8]}"
        
        # Create first terminal
        dto1 = TerminalCreateRequestDTO(
            branch_id=str(branch.branch_id),
            name="Terminal 1",
            code=f"TT-{uuid.uuid4().hex[:6]}",
            device_id=device_id,
        )
        
        created1 = terminal_service.create_terminal(org_id, user_id, dto1)
        
        # Try to create second terminal with same device_id (even in different org)
        other_org_id = f"test-org-{uuid.uuid4()}"
        dto2 = TerminalCreateRequestDTO(
            branch_id=str(branch.branch_id),
            name="Terminal 2",
            code=f"TT-{uuid.uuid4().hex[:6]}",
            device_id=device_id,
        )
        
        with pytest.raises(ValueError, match="already registered"):
            terminal_service.create_terminal(other_org_id, user_id, dto2)
        
        # Cleanup
        with TerminalRepository() as repo:
            repo.delete(created1.terminal_id)

    def test_branch_validation(self, test_branch):
        """Test that terminal creation validates branch existence."""
        branch, org_id, user_id = test_branch
        
        # Try to create terminal with non-existent branch
        dto = TerminalCreateRequestDTO(
            branch_id=str(uuid.uuid4()),
            name="Terminal",
            code=f"TT-{uuid.uuid4().hex[:6]}",
        )
        
        with pytest.raises(ValueError, match="does not exist or does not belong"):
            terminal_service.create_terminal(org_id, user_id, dto)
