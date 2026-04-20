"""
Unit tests for dashboard repository data access methods.
These tests verify repository methods with mocked database calls.

**Validates: Requirements 6.1, 6.2, 11.1, 11.2, 11.5**
"""
import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, timezone
import uuid

from app.repositories.dashboard_repository import DashboardRepository


class TestDashboardRepositoryUnit:
    """Unit tests for dashboard repository methods."""

    @patch('app.repositories.dashboard_repository.DatabaseConnection.__init__')
    def test_get_active_sessions_without_filter(self, mock_db_init):
        """
        Test that get_active_sessions retrieves all active sessions for an organization.
        
        **Validates: Requirement 6.1**
        """
        # Setup mock
        mock_db_init.return_value = None
        repo = DashboardRepository()
        
        # Mock session and execute
        mock_session = MagicMock()
        repo.session = mock_session
        
        # Mock query result
        mock_row1 = Mock()
        mock_row1.session_id = uuid.uuid4()
        mock_row1.name = "Session 1"
        mock_row1.type = "match"
        mock_row1.context = "gradas"
        
        mock_row2 = Mock()
        mock_row2.session_id = uuid.uuid4()
        mock_row2.name = "Session 2"
        mock_row2.type = "shift"
        mock_row2.context = "mesa"
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row1, mock_row2]
        mock_session.execute.return_value = mock_result
        
        # Call repository method
        result = repo.get_active_sessions("org-123")
        
        # Verify result
        assert len(result) == 2
        assert result[0]["session_id"] == str(mock_row1.session_id)
        assert result[0]["name"] == "Session 1"
        assert result[0]["type"] == "match"
        assert result[0]["context"] == "gradas"
        assert result[1]["session_id"] == str(mock_row2.session_id)
        assert result[1]["name"] == "Session 2"
        
        # Verify query was called correctly
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args
        assert "org-123" in str(call_args)

    @patch('app.repositories.dashboard_repository.DatabaseConnection.__init__')
    def test_get_active_sessions_with_session_id_filter(self, mock_db_init):
        """
        Test that get_active_sessions filters by session_id when provided.
        
        **Validates: Requirement 6.2**
        """
        # Setup mock
        mock_db_init.return_value = None
        repo = DashboardRepository()
        
        # Mock session and execute
        mock_session = MagicMock()
        repo.session = mock_session
        
        # Mock query result with single session
        mock_row = Mock()
        mock_row.session_id = uuid.uuid4()
        mock_row.name = "Specific Session"
        mock_row.type = "match"
        mock_row.context = "gradas"
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result
        
        # Call repository method with session_id filter
        result = repo.get_active_sessions("org-123", session_id="session-specific")
        
        # Verify result
        assert len(result) == 1
        assert result[0]["session_id"] == str(mock_row.session_id)
        
        # Verify query was called with session_id parameter
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args
        assert "session-specific" in str(call_args)

    @patch('app.repositories.dashboard_repository.DatabaseConnection.__init__')
    def test_get_active_sessions_empty_result(self, mock_db_init):
        """
        Test that get_active_sessions returns empty list when no sessions found.
        
        **Validates: Requirement 6.1**
        """
        # Setup mock
        mock_db_init.return_value = None
        repo = DashboardRepository()
        
        # Mock session and execute
        mock_session = MagicMock()
        repo.session = mock_session
        
        # Mock empty query result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result
        
        # Call repository method
        result = repo.get_active_sessions("org-123")
        
        # Verify empty result
        assert result == []

    @patch('app.repositories.dashboard_repository.DatabaseConnection.__init__')
    def test_get_active_assignments_for_sessions(self, mock_db_init):
        """
        Test that get_active_assignments_for_sessions retrieves assignments with branch and cashier info.
        
        **Validates: Requirement 11.1**
        """
        # Setup mock
        mock_db_init.return_value = None
        repo = DashboardRepository()
        
        # Mock session and execute
        mock_session = MagicMock()
        repo.session = mock_session
        
        # Mock query result
        mock_row1 = Mock()
        mock_row1.assignment_id = uuid.uuid4()
        mock_row1.session_id = uuid.uuid4()
        mock_row1.branch_id = uuid.uuid4()
        mock_row1.branch_name = "Puesto 1"
        mock_row1.branch_code = "P1"
        mock_row1.cashier_id = "cashier-1"
        mock_row1.cashier_name = "cashier-1"
        
        mock_row2 = Mock()
        mock_row2.assignment_id = uuid.uuid4()
        mock_row2.session_id = uuid.uuid4()
        mock_row2.branch_id = uuid.uuid4()
        mock_row2.branch_name = "Puesto 2"
        mock_row2.branch_code = "P2"
        mock_row2.cashier_id = "cashier-2"
        mock_row2.cashier_name = "cashier-2"
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row1, mock_row2]
        mock_session.execute.return_value = mock_result
        
        # Call repository method
        session_ids = ["session-1", "session-2"]
        result = repo.get_active_assignments_for_sessions(session_ids)
        
        # Verify result
        assert len(result) == 2
        assert result[0]["assignment_id"] == str(mock_row1.assignment_id)
        assert result[0]["branch_name"] == "Puesto 1"
        assert result[0]["branch_code"] == "P1"
        assert result[0]["cashier_id"] == "cashier-1"
        assert result[1]["assignment_id"] == str(mock_row2.assignment_id)
        assert result[1]["branch_name"] == "Puesto 2"

    @patch('app.repositories.dashboard_repository.DatabaseConnection.__init__')
    def test_get_active_assignments_for_sessions_empty_list(self, mock_db_init):
        """
        Test that get_active_assignments_for_sessions returns empty list when given empty session list.
        
        **Validates: Requirement 11.1**
        """
        # Setup mock
        mock_db_init.return_value = None
        repo = DashboardRepository()
        
        # Call repository method with empty list
        result = repo.get_active_assignments_for_sessions([])
        
        # Verify empty result
        assert result == []

    @patch('app.repositories.dashboard_repository.DatabaseConnection.__init__')
    def test_aggregate_sales_by_assignment(self, mock_db_init):
        """
        Test that aggregate_sales_by_assignment correctly aggregates sales data.
        
        **Validates: Requirements 11.1, 11.2**
        """
        # Setup mock
        mock_db_init.return_value = None
        repo = DashboardRepository()
        
        # Mock session and execute
        mock_session = MagicMock()
        repo.session = mock_session
        
        # Mock query result
        assignment_id_1 = uuid.uuid4()
        assignment_id_2 = uuid.uuid4()
        
        mock_row1 = Mock()
        mock_row1.assignment_id = assignment_id_1
        mock_row1.sales_count = 10
        mock_row1.total_revenue = 50000.0
        mock_row1.cash = 20000.0
        mock_row1.sinpe = 15000.0
        mock_row1.card = 15000.0
        mock_row1.last_sync_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        mock_row2 = Mock()
        mock_row2.assignment_id = assignment_id_2
        mock_row2.sales_count = 5
        mock_row2.total_revenue = 25000.0
        mock_row2.cash = 10000.0
        mock_row2.sinpe = 8000.0
        mock_row2.card = 7000.0
        mock_row2.last_sync_at = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row1, mock_row2]
        mock_session.execute.return_value = mock_result
        
        # Call repository method
        assignment_ids = [str(assignment_id_1), str(assignment_id_2)]
        result = repo.aggregate_sales_by_assignment(assignment_ids)
        
        # Verify result
        assert len(result) == 2
        assert str(assignment_id_1) in result
        assert str(assignment_id_2) in result
        
        # Verify first assignment data
        assert result[str(assignment_id_1)]["sales_count"] == 10
        assert result[str(assignment_id_1)]["total_revenue"] == 50000.0
        assert result[str(assignment_id_1)]["cash"] == 20000.0
        assert result[str(assignment_id_1)]["sinpe"] == 15000.0
        assert result[str(assignment_id_1)]["card"] == 15000.0
        assert result[str(assignment_id_1)]["last_sync_at"] == 1704110400
        
        # Verify second assignment data
        assert result[str(assignment_id_2)]["sales_count"] == 5
        assert result[str(assignment_id_2)]["total_revenue"] == 25000.0

    @patch('app.repositories.dashboard_repository.DatabaseConnection.__init__')
    def test_aggregate_sales_by_assignment_empty_list(self, mock_db_init):
        """
        Test that aggregate_sales_by_assignment returns empty dict when given empty assignment list.
        
        **Validates: Requirement 11.1**
        """
        # Setup mock
        mock_db_init.return_value = None
        repo = DashboardRepository()
        
        # Call repository method with empty list
        result = repo.aggregate_sales_by_assignment([])
        
        # Verify empty result
        assert result == {}

    @patch('app.repositories.dashboard_repository.DatabaseConnection.__init__')
    def test_aggregate_sales_by_assignment_no_sales(self, mock_db_init):
        """
        Test that aggregate_sales_by_assignment handles assignments with no sales.
        
        **Validates: Requirement 11.1**
        """
        # Setup mock
        mock_db_init.return_value = None
        repo = DashboardRepository()
        
        # Mock session and execute
        mock_session = MagicMock()
        repo.session = mock_session
        
        # Mock query result with zero sales
        assignment_id = uuid.uuid4()
        
        mock_row = Mock()
        mock_row.assignment_id = assignment_id
        mock_row.sales_count = 0
        mock_row.total_revenue = 0.0
        mock_row.cash = 0.0
        mock_row.sinpe = 0.0
        mock_row.card = 0.0
        mock_row.last_sync_at = None
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result
        
        # Call repository method
        result = repo.aggregate_sales_by_assignment([str(assignment_id)])
        
        # Verify result has zero values
        assert str(assignment_id) in result
        assert result[str(assignment_id)]["sales_count"] == 0
        assert result[str(assignment_id)]["total_revenue"] == 0.0
        assert result[str(assignment_id)]["last_sync_at"] == 0

    @patch('app.repositories.dashboard_repository.DatabaseConnection.__init__')
    def test_calculate_product_ranking(self, mock_db_init):
        """
        Test that calculate_product_ranking returns top products by revenue.
        
        **Validates: Requirement 11.5**
        """
        # Setup mock
        mock_db_init.return_value = None
        repo = DashboardRepository()
        
        # Mock session and execute
        mock_session = MagicMock()
        repo.session = mock_session
        
        # Mock query result with products
        mock_row1 = Mock()
        mock_row1.name = "Cerveza"
        mock_row1.emoji = "🍺"
        mock_row1.units = 50
        mock_row1.revenue = 25000.0
        
        mock_row2 = Mock()
        mock_row2.name = "Refresco"
        mock_row2.emoji = "🥤"
        mock_row2.units = 30
        mock_row2.revenue = 15000.0
        
        mock_row3 = Mock()
        mock_row3.name = "Hot Dog"
        mock_row3.emoji = "🌭"
        mock_row3.units = 20
        mock_row3.revenue = 10000.0
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row1, mock_row2, mock_row3]
        mock_session.execute.return_value = mock_result
        
        # Call repository method
        session_ids = ["session-1"]
        result = repo.calculate_product_ranking(session_ids, limit=10)
        
        # Verify result
        assert len(result) == 3
        assert result[0]["name"] == "Cerveza"
        assert result[0]["emoji"] == "🍺"
        assert result[0]["units"] == 50
        assert result[0]["revenue"] == 25000.0
        assert result[1]["name"] == "Refresco"
        assert result[2]["name"] == "Hot Dog"
        
        # Verify query was called with limit
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args
        assert "10" in str(call_args) or 10 in call_args[0][1].values()

    @patch('app.repositories.dashboard_repository.DatabaseConnection.__init__')
    def test_calculate_product_ranking_with_limit(self, mock_db_init):
        """
        Test that calculate_product_ranking respects the limit parameter.
        
        **Validates: Requirement 11.5**
        """
        # Setup mock
        mock_db_init.return_value = None
        repo = DashboardRepository()
        
        # Mock session and execute
        mock_session = MagicMock()
        repo.session = mock_session
        
        # Mock query result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result
        
        # Call repository method with custom limit
        session_ids = ["session-1"]
        repo.calculate_product_ranking(session_ids, limit=5)
        
        # Verify query was called with custom limit
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args
        assert "5" in str(call_args) or 5 in call_args[0][1].values()

    @patch('app.repositories.dashboard_repository.DatabaseConnection.__init__')
    def test_calculate_product_ranking_empty_sessions(self, mock_db_init):
        """
        Test that calculate_product_ranking returns empty list when given empty session list.
        
        **Validates: Requirement 11.5**
        """
        # Setup mock
        mock_db_init.return_value = None
        repo = DashboardRepository()
        
        # Call repository method with empty list
        result = repo.calculate_product_ranking([], limit=10)
        
        # Verify empty result
        assert result == []

    @patch('app.repositories.dashboard_repository.DatabaseConnection.__init__')
    def test_calculate_product_ranking_handles_null_emoji(self, mock_db_init):
        """
        Test that calculate_product_ranking handles null emoji values.
        
        **Validates: Requirement 11.5**
        """
        # Setup mock
        mock_db_init.return_value = None
        repo = DashboardRepository()
        
        # Mock session and execute
        mock_session = MagicMock()
        repo.session = mock_session
        
        # Mock query result with null emoji
        mock_row = Mock()
        mock_row.name = "Product"
        mock_row.emoji = None
        mock_row.units = 10
        mock_row.revenue = 5000.0
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result
        
        # Call repository method
        result = repo.calculate_product_ranking(["session-1"], limit=10)
        
        # Verify emoji defaults to empty string
        assert len(result) == 1
        assert result[0]["emoji"] == ""

    @patch('app.repositories.dashboard_repository.DatabaseConnection.__init__')
    def test_aggregate_sales_by_assignment_handles_null_values(self, mock_db_init):
        """
        Test that aggregate_sales_by_assignment handles null values correctly.
        
        **Validates: Requirement 11.2**
        """
        # Setup mock
        mock_db_init.return_value = None
        repo = DashboardRepository()
        
        # Mock session and execute
        mock_session = MagicMock()
        repo.session = mock_session
        
        # Mock query result with null values
        assignment_id = uuid.uuid4()
        
        mock_row = Mock()
        mock_row.assignment_id = assignment_id
        mock_row.sales_count = None
        mock_row.total_revenue = None
        mock_row.cash = None
        mock_row.sinpe = None
        mock_row.card = None
        mock_row.last_sync_at = None
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result
        
        # Call repository method
        result = repo.aggregate_sales_by_assignment([str(assignment_id)])
        
        # Verify null values are converted to 0
        assert result[str(assignment_id)]["sales_count"] == 0
        assert result[str(assignment_id)]["total_revenue"] == 0.0
        assert result[str(assignment_id)]["cash"] == 0.0
        assert result[str(assignment_id)]["sinpe"] == 0.0
        assert result[str(assignment_id)]["card"] == 0.0
        assert result[str(assignment_id)]["last_sync_at"] == 0

    @patch('app.repositories.dashboard_repository.DatabaseConnection.__init__')
    def test_calculate_product_ranking_handles_null_units_and_revenue(self, mock_db_init):
        """
        Test that calculate_product_ranking handles null units and revenue values.
        
        **Validates: Requirement 11.5**
        """
        # Setup mock
        mock_db_init.return_value = None
        repo = DashboardRepository()
        
        # Mock session and execute
        mock_session = MagicMock()
        repo.session = mock_session
        
        # Mock query result with null values
        mock_row = Mock()
        mock_row.name = "Product"
        mock_row.emoji = "📦"
        mock_row.units = None
        mock_row.revenue = None
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result
        
        # Call repository method
        result = repo.calculate_product_ranking(["session-1"], limit=10)
        
        # Verify null values are converted to 0
        assert len(result) == 1
        assert result[0]["units"] == 0
        assert result[0]["revenue"] == 0.0
