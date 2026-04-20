"""
Unit tests for dashboard service business logic.
These tests verify service methods without requiring database access.

**Validates: Requirements 6.1, 6.2, 11.1, 11.2, 11.3, 11.4, 11.5**
"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from app.services import dashboard_service


class TestDashboardServiceUnit:
    """Unit tests for dashboard service methods."""

    @patch('app.services.dashboard_service.DashboardRepository')
    def test_get_dashboard_data_no_active_sessions(self, mock_repo_class):
        """
        Test that get_dashboard_data returns empty dashboard when no active sessions exist.
        
        **Validates: Requirement 6.1**
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        mock_repo.get_active_sessions.return_value = []
        
        # Call service
        result = dashboard_service.get_dashboard_data("org-123", "user-123")
        
        # Verify empty dashboard
        assert result.stands == []
        assert result.total_revenue == 0.0
        assert result.total_sales == 0
        assert result.avg_ticket == 0.0
        assert result.product_ranking == []
        
        # Verify repository was called correctly
        mock_repo.get_active_sessions.assert_called_once_with("org-123", None)

    @patch('app.services.dashboard_service.DashboardRepository')
    def test_get_dashboard_data_no_active_assignments(self, mock_repo_class):
        """
        Test that get_dashboard_data returns empty dashboard when no active assignments exist.
        
        **Validates: Requirement 6.1**
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        # Mock sessions exist but no assignments
        mock_repo.get_active_sessions.return_value = [
            {
                "session_id": "session-1",
                "name": "Test Session",
                "type": "match",
                "context": "gradas",
            }
        ]
        mock_repo.get_active_assignments_for_sessions.return_value = []
        
        # Call service
        result = dashboard_service.get_dashboard_data("org-123", "user-123")
        
        # Verify empty dashboard
        assert result.stands == []
        assert result.total_revenue == 0.0
        assert result.total_sales == 0
        assert result.avg_ticket == 0.0
        assert result.product_ranking == []

    @patch('app.services.dashboard_service.DashboardRepository')
    def test_get_dashboard_data_single_session_with_assignments(self, mock_repo_class):
        """
        Test that get_dashboard_data correctly aggregates data for a single session with assignments.
        
        **Validates: Requirements 6.1, 11.1, 11.2, 11.3**
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        # Mock sessions
        mock_repo.get_active_sessions.return_value = [
            {
                "session_id": "session-1",
                "name": "Test Session",
                "type": "match",
                "context": "gradas",
            }
        ]
        
        # Mock assignments
        mock_repo.get_active_assignments_for_sessions.return_value = [
            {
                "assignment_id": "assignment-1",
                "session_id": "session-1",
                "branch_id": "branch-1",
                "branch_name": "Puesto 1",
                "branch_code": "P1",
                "cashier_id": "cashier-1",
                "cashier_name": "Juan Perez",
            }
        ]
        
        # Mock sales data
        mock_repo.aggregate_sales_by_assignment.return_value = {
            "assignment-1": {
                "sales_count": 10,
                "total_revenue": 50000.0,
                "cash": 20000.0,
                "sinpe": 15000.0,
                "card": 15000.0,
                "last_sync_at": 1234567890,
            }
        }
        
        # Mock product ranking
        mock_repo.calculate_product_ranking.return_value = [
            {
                "name": "Cerveza",
                "emoji": "🍺",
                "units": 50,
                "revenue": 25000.0,
            }
        ]
        
        # Call service
        result = dashboard_service.get_dashboard_data("org-123", "user-123")
        
        # Verify stands data
        assert len(result.stands) == 1
        stand = result.stands[0]
        assert stand.id == "branch-1"
        assert stand.name == "Puesto 1"
        assert stand.cashier_name == "Juan Perez"
        assert stand.context == "gradas"
        assert stand.total_revenue == 50000.0
        assert stand.sales_count == 10
        assert stand.cash == 20000.0
        assert stand.sinpe == 15000.0
        assert stand.card == 15000.0
        assert stand.last_sync_at == 1234567890
        
        # Verify totals
        assert result.total_revenue == 50000.0
        assert result.total_sales == 10
        assert result.avg_ticket == 5000.0
        
        # Verify product ranking
        assert len(result.product_ranking) == 1
        assert result.product_ranking[0].name == "Cerveza"
        assert result.product_ranking[0].emoji == "🍺"
        assert result.product_ranking[0].units == 50
        assert result.product_ranking[0].revenue == 25000.0

    @patch('app.services.dashboard_service.DashboardRepository')
    def test_get_dashboard_data_multiple_sessions_with_assignments(self, mock_repo_class):
        """
        Test that get_dashboard_data correctly aggregates data for multiple sessions.
        
        **Validates: Requirements 6.1, 11.1, 11.2, 11.3**
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        # Mock multiple sessions
        mock_repo.get_active_sessions.return_value = [
            {
                "session_id": "session-1",
                "name": "Session 1",
                "type": "match",
                "context": "gradas",
            },
            {
                "session_id": "session-2",
                "name": "Session 2",
                "type": "shift",
                "context": "mesa",
            }
        ]
        
        # Mock multiple assignments
        mock_repo.get_active_assignments_for_sessions.return_value = [
            {
                "assignment_id": "assignment-1",
                "session_id": "session-1",
                "branch_id": "branch-1",
                "branch_name": "Puesto 1",
                "branch_code": "P1",
                "cashier_id": "cashier-1",
                "cashier_name": "Juan Perez",
            },
            {
                "assignment_id": "assignment-2",
                "session_id": "session-2",
                "branch_id": "branch-2",
                "branch_name": "Puesto 2",
                "branch_code": "P2",
                "cashier_id": "cashier-2",
                "cashier_name": "Maria Lopez",
            }
        ]
        
        # Mock sales data for both assignments
        mock_repo.aggregate_sales_by_assignment.return_value = {
            "assignment-1": {
                "sales_count": 10,
                "total_revenue": 50000.0,
                "cash": 20000.0,
                "sinpe": 15000.0,
                "card": 15000.0,
                "last_sync_at": 1234567890,
            },
            "assignment-2": {
                "sales_count": 15,
                "total_revenue": 75000.0,
                "cash": 30000.0,
                "sinpe": 25000.0,
                "card": 20000.0,
                "last_sync_at": 1234567900,
            }
        }
        
        # Mock product ranking
        mock_repo.calculate_product_ranking.return_value = []
        
        # Call service
        result = dashboard_service.get_dashboard_data("org-123", "user-123")
        
        # Verify stands data
        assert len(result.stands) == 2
        
        # Verify totals are aggregated correctly
        assert result.total_revenue == 125000.0
        assert result.total_sales == 25
        assert result.avg_ticket == 5000.0

    @patch('app.services.dashboard_service.DashboardRepository')
    def test_get_dashboard_data_with_session_filter(self, mock_repo_class):
        """
        Test that get_dashboard_data filters by session_id when provided.
        
        **Validates: Requirement 6.2**
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        # Mock filtered session
        mock_repo.get_active_sessions.return_value = [
            {
                "session_id": "session-specific",
                "name": "Specific Session",
                "type": "match",
                "context": "gradas",
            }
        ]
        
        mock_repo.get_active_assignments_for_sessions.return_value = []
        
        # Call service with session_id filter
        dashboard_service.get_dashboard_data("org-123", "user-123", session_id="session-specific")
        
        # Verify repository was called with session_id
        mock_repo.get_active_sessions.assert_called_once_with("org-123", "session-specific")

    @patch('app.services.dashboard_service.DashboardRepository')
    def test_get_dashboard_data_zero_sales_avg_ticket(self, mock_repo_class):
        """
        Test that get_dashboard_data handles zero sales case (avg_ticket = 0).
        
        **Validates: Requirement 11.4**
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        # Mock sessions and assignments but no sales
        mock_repo.get_active_sessions.return_value = [
            {
                "session_id": "session-1",
                "name": "Test Session",
                "type": "match",
                "context": "gradas",
            }
        ]
        
        mock_repo.get_active_assignments_for_sessions.return_value = [
            {
                "assignment_id": "assignment-1",
                "session_id": "session-1",
                "branch_id": "branch-1",
                "branch_name": "Puesto 1",
                "branch_code": "P1",
                "cashier_id": "cashier-1",
                "cashier_name": "Juan Perez",
            }
        ]
        
        # Mock zero sales
        mock_repo.aggregate_sales_by_assignment.return_value = {
            "assignment-1": {
                "sales_count": 0,
                "total_revenue": 0.0,
                "cash": 0.0,
                "sinpe": 0.0,
                "card": 0.0,
                "last_sync_at": 0,
            }
        }
        
        mock_repo.calculate_product_ranking.return_value = []
        
        # Call service
        result = dashboard_service.get_dashboard_data("org-123", "user-123")
        
        # Verify avg_ticket is 0 when no sales
        assert result.total_revenue == 0.0
        assert result.total_sales == 0
        assert result.avg_ticket == 0.0

    @patch('app.services.dashboard_service.DashboardRepository')
    def test_get_dashboard_data_sales_aggregation(self, mock_repo_class):
        """
        Test that get_dashboard_data correctly aggregates sales across multiple stands.
        
        **Validates: Requirements 11.2, 11.3**
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        # Mock sessions
        mock_repo.get_active_sessions.return_value = [
            {
                "session_id": "session-1",
                "name": "Test Session",
                "type": "match",
                "context": "gradas",
            }
        ]
        
        # Mock three assignments
        mock_repo.get_active_assignments_for_sessions.return_value = [
            {
                "assignment_id": "assignment-1",
                "session_id": "session-1",
                "branch_id": "branch-1",
                "branch_name": "Puesto 1",
                "branch_code": "P1",
                "cashier_id": "cashier-1",
                "cashier_name": "Cashier 1",
            },
            {
                "assignment_id": "assignment-2",
                "session_id": "session-1",
                "branch_id": "branch-2",
                "branch_name": "Puesto 2",
                "branch_code": "P2",
                "cashier_id": "cashier-2",
                "cashier_name": "Cashier 2",
            },
            {
                "assignment_id": "assignment-3",
                "session_id": "session-1",
                "branch_id": "branch-3",
                "branch_name": "Puesto 3",
                "branch_code": "P3",
                "cashier_id": "cashier-3",
                "cashier_name": "Cashier 3",
            }
        ]
        
        # Mock sales data with different amounts
        mock_repo.aggregate_sales_by_assignment.return_value = {
            "assignment-1": {
                "sales_count": 5,
                "total_revenue": 25000.0,
                "cash": 10000.0,
                "sinpe": 10000.0,
                "card": 5000.0,
                "last_sync_at": 1234567890,
            },
            "assignment-2": {
                "sales_count": 8,
                "total_revenue": 40000.0,
                "cash": 15000.0,
                "sinpe": 15000.0,
                "card": 10000.0,
                "last_sync_at": 1234567891,
            },
            "assignment-3": {
                "sales_count": 12,
                "total_revenue": 60000.0,
                "cash": 20000.0,
                "sinpe": 20000.0,
                "card": 20000.0,
                "last_sync_at": 1234567892,
            }
        }
        
        mock_repo.calculate_product_ranking.return_value = []
        
        # Call service
        result = dashboard_service.get_dashboard_data("org-123", "user-123")
        
        # Verify aggregation
        assert result.total_revenue == 125000.0
        assert result.total_sales == 25
        assert result.avg_ticket == 5000.0

    @patch('app.services.dashboard_service.DashboardRepository')
    def test_get_dashboard_data_payment_method_breakdown(self, mock_repo_class):
        """
        Test that get_dashboard_data correctly breaks down payment methods.
        
        **Validates: Requirement 11.2**
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        # Mock sessions
        mock_repo.get_active_sessions.return_value = [
            {
                "session_id": "session-1",
                "name": "Test Session",
                "type": "match",
                "context": "gradas",
            }
        ]
        
        # Mock assignment
        mock_repo.get_active_assignments_for_sessions.return_value = [
            {
                "assignment_id": "assignment-1",
                "session_id": "session-1",
                "branch_id": "branch-1",
                "branch_name": "Puesto 1",
                "branch_code": "P1",
                "cashier_id": "cashier-1",
                "cashier_name": "Juan Perez",
            }
        ]
        
        # Mock sales with specific payment breakdown
        mock_repo.aggregate_sales_by_assignment.return_value = {
            "assignment-1": {
                "sales_count": 10,
                "total_revenue": 100000.0,
                "cash": 40000.0,
                "sinpe": 35000.0,
                "card": 25000.0,
                "last_sync_at": 1234567890,
            }
        }
        
        mock_repo.calculate_product_ranking.return_value = []
        
        # Call service
        result = dashboard_service.get_dashboard_data("org-123", "user-123")
        
        # Verify payment breakdown
        stand = result.stands[0]
        assert stand.cash == 40000.0
        assert stand.sinpe == 35000.0
        assert stand.card == 25000.0
        assert stand.total_revenue == 100000.0

    @patch('app.services.dashboard_service.DashboardRepository')
    def test_get_dashboard_data_product_ranking(self, mock_repo_class):
        """
        Test that get_dashboard_data correctly retrieves product ranking.
        
        **Validates: Requirement 11.5**
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        # Mock sessions
        mock_repo.get_active_sessions.return_value = [
            {
                "session_id": "session-1",
                "name": "Test Session",
                "type": "match",
                "context": "gradas",
            }
        ]
        
        # Mock assignment
        mock_repo.get_active_assignments_for_sessions.return_value = [
            {
                "assignment_id": "assignment-1",
                "session_id": "session-1",
                "branch_id": "branch-1",
                "branch_name": "Puesto 1",
                "branch_code": "P1",
                "cashier_id": "cashier-1",
                "cashier_name": "Juan Perez",
            }
        ]
        
        mock_repo.aggregate_sales_by_assignment.return_value = {
            "assignment-1": {
                "sales_count": 10,
                "total_revenue": 50000.0,
                "cash": 20000.0,
                "sinpe": 15000.0,
                "card": 15000.0,
                "last_sync_at": 1234567890,
            }
        }
        
        # Mock product ranking with multiple products
        mock_repo.calculate_product_ranking.return_value = [
            {"name": "Cerveza", "emoji": "🍺", "units": 50, "revenue": 25000.0},
            {"name": "Refresco", "emoji": "🥤", "units": 30, "revenue": 15000.0},
            {"name": "Hot Dog", "emoji": "🌭", "units": 20, "revenue": 10000.0},
        ]
        
        # Call service
        result = dashboard_service.get_dashboard_data("org-123", "user-123")
        
        # Verify product ranking
        assert len(result.product_ranking) == 3
        assert result.product_ranking[0].name == "Cerveza"
        assert result.product_ranking[0].units == 50
        assert result.product_ranking[0].revenue == 25000.0
        assert result.product_ranking[1].name == "Refresco"
        assert result.product_ranking[2].name == "Hot Dog"
        
        # Verify repository was called with limit=10
        mock_repo.calculate_product_ranking.assert_called_once_with(["session-1"], limit=10)

    @patch('app.services.dashboard_service.DashboardRepository')
    def test_get_dashboard_data_assignment_without_sales(self, mock_repo_class):
        """
        Test that get_dashboard_data handles assignments with no sales data.
        
        **Validates: Requirement 11.1**
        """
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value.__enter__.return_value = mock_repo
        
        # Mock sessions
        mock_repo.get_active_sessions.return_value = [
            {
                "session_id": "session-1",
                "name": "Test Session",
                "type": "match",
                "context": "gradas",
            }
        ]
        
        # Mock assignment
        mock_repo.get_active_assignments_for_sessions.return_value = [
            {
                "assignment_id": "assignment-1",
                "session_id": "session-1",
                "branch_id": "branch-1",
                "branch_name": "Puesto 1",
                "branch_code": "P1",
                "cashier_id": "cashier-1",
                "cashier_name": "Juan Perez",
            }
        ]
        
        # Mock empty sales data (assignment not in the map)
        mock_repo.aggregate_sales_by_assignment.return_value = {}
        
        mock_repo.calculate_product_ranking.return_value = []
        
        # Call service
        result = dashboard_service.get_dashboard_data("org-123", "user-123")
        
        # Verify stand has zero values
        assert len(result.stands) == 1
        stand = result.stands[0]
        assert stand.total_revenue == 0.0
        assert stand.sales_count == 0
        assert stand.cash == 0.0
        assert stand.sinpe == 0.0
        assert stand.card == 0.0
        assert stand.last_sync_at == 0
