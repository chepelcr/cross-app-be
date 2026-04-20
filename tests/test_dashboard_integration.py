"""
Integration tests for dashboard handler with real database operations.
"""
import pytest
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.configuration.fast_api_config import FastApiConfig
from app.models.session import Session
from app.models.branch import Branch
from app.models.assignment import Assignment
from app.repositories.session_repository import SessionRepository
from app.repositories.branch_repository import BranchRepository
from app.repositories.assignment_repository import AssignmentRepository
from app.services import dashboard_service
from app.configuration.database_connection import DatabaseConnection


@pytest.mark.integration
class TestDashboardIntegration:
    """Integration tests for dashboard operations with database."""

    @pytest.fixture
    def setup_sales_orders_table(self):
        """Create a temporary sales_orders table for testing."""
        with DatabaseConnection() as db:
            # Create the sales_orders table if it doesn't exist
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS sales_orders (
                    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    assignment_id UUID NOT NULL,
                    session_id UUID,
                    payment_method VARCHAR(50),
                    total DECIMAL(12, 2),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create order_items table for product ranking
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS order_items (
                    order_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    order_id UUID NOT NULL,
                    product_id UUID NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price DECIMAL(12, 2) NOT NULL
                )
            """))
            
            db.session.commit()
        
        yield
        
        # Cleanup: Drop the tables after tests
        with DatabaseConnection() as db:
            db.session.execute(text("DROP TABLE IF EXISTS order_items CASCADE"))
            db.session.execute(text("DROP TABLE IF EXISTS sales_orders CASCADE"))
            db.session.commit()

    @pytest.fixture
    def test_setup(self, setup_sales_orders_table, test_organization):
        """Create test data: organization, branch, session, and assignment."""
        org_id = test_organization["id"]
        user_id = test_organization["user_id"]
        
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

    def test_get_dashboard_no_active_sessions(self, test_organization):
        """Test getting dashboard when no active sessions exist."""
        org_id = test_organization["id"]
        user_id = test_organization["user_id"]
        
        # Get dashboard data
        dashboard = dashboard_service.get_dashboard_data(org_id, user_id)
        
        # Verify empty dashboard
        assert dashboard is not None
        assert dashboard.stands == []
        assert dashboard.total_revenue == 0.0
        assert dashboard.total_sales == 0
        assert dashboard.avg_ticket == 0.0
        assert dashboard.product_ranking == []

    def test_get_dashboard_no_active_assignments(self, setup_sales_orders_table, test_organization):
        """Test getting dashboard when session exists but no active assignments."""
        org_id = test_organization["id"]
        user_id = test_organization["user_id"]
        
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
        
        # Create session without assignments
        with SessionRepository() as repo:
            session = Session(
                session_id=uuid.uuid4(),
                organization_id=org_id,
                branch_id=branch.branch_id,
                name="Empty Session",
                type="match",
                context="gradas",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            session = repo.save(session)
        
        # Get dashboard data
        dashboard = dashboard_service.get_dashboard_data(org_id, user_id)
        
        # Verify empty dashboard
        assert dashboard is not None
        assert dashboard.stands == []
        assert dashboard.total_revenue == 0.0
        assert dashboard.total_sales == 0
        assert dashboard.avg_ticket == 0.0
        assert dashboard.product_ranking == []
        
        # Cleanup
        with SessionRepository() as repo:
            repo.delete(str(session.session_id))
        with BranchRepository() as repo:
            repo.delete(str(branch.branch_id))

    def test_get_dashboard_single_session_with_sales(self, test_setup):
        """Test getting dashboard with a single session and sales data."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Insert sales orders
        with DatabaseConnection() as db:
            db.session.execute(text("""
                INSERT INTO sales_orders (assignment_id, session_id, payment_method, total)
                VALUES 
                    (:assignment_id, :session_id, 'cash', 100.00),
                    (:assignment_id, :session_id, 'sinpe', 150.00),
                    (:assignment_id, :session_id, 'card', 200.00)
            """), {
                "assignment_id": str(assignment.assignment_id),
                "session_id": str(session.session_id)
            })
            db.session.commit()
        
        # Get dashboard data
        dashboard = dashboard_service.get_dashboard_data(org_id, user_id)
        
        # Verify dashboard data
        assert dashboard is not None
        assert len(dashboard.stands) == 1
        
        stand = dashboard.stands[0]
        assert stand.id == str(branch.branch_id)
        assert stand.name == "Test Branch"
        assert stand.cashier_name == user_id
        assert stand.context == "gradas"
        assert stand.total_revenue == 450.0
        assert stand.sales_count == 3
        assert stand.cash == 100.0
        assert stand.sinpe == 150.0
        assert stand.card == 200.0
        assert stand.last_sync_at > 0
        
        # Verify global KPIs
        assert dashboard.total_revenue == 450.0
        assert dashboard.total_sales == 3
        assert dashboard.avg_ticket == 150.0
        
        # Cleanup sales orders
        with DatabaseConnection() as db:
            db.session.execute(text("""
                DELETE FROM sales_orders WHERE assignment_id = :assignment_id
            """), {"assignment_id": str(assignment.assignment_id)})
            db.session.commit()

    def test_get_dashboard_multiple_sessions_with_assignments(self, setup_sales_orders_table, test_organization):
        """Test getting dashboard with multiple sessions and assignments."""
        org_id = test_organization["id"]
        user_id = test_organization["user_id"]
        
        # Create branches
        branches = []
        with BranchRepository() as repo:
            for i in range(2):
                branch = Branch(
                    branch_id=uuid.uuid4(),
                    organization_id=org_id,
                    name=f"Branch {i+1}",
                    code=f"B{i+1}-{uuid.uuid4().hex[:4]}",
                    type="stand",
                    is_active=True,
                    created_by=user_id,
                )
                branch = repo.save(branch)
                branches.append(branch)
        
        # Create sessions
        sessions = []
        with SessionRepository() as repo:
            for i, branch in enumerate(branches):
                session = Session(
                    session_id=uuid.uuid4(),
                    organization_id=org_id,
                    branch_id=branch.branch_id,
                    name=f"Session {i+1}",
                    type="match",
                    context="gradas" if i == 0 else "mesa",
                    start_time=datetime.now(timezone.utc),
                    is_active=True,
                    created_by=user_id,
                )
                session = repo.save(session)
                sessions.append(session)
        
        # Create assignments
        assignments = []
        with AssignmentRepository() as repo:
            for i, (session, branch) in enumerate(zip(sessions, branches)):
                assignment = Assignment(
                    assignment_id=uuid.uuid4(),
                    organization_id=org_id,
                    session_id=session.session_id,
                    user_id=f"cashier-{i+1}",
                    branch_id=branch.branch_id,
                    terminal_id=None,
                    role="cashier",
                    start_time=datetime.now(timezone.utc),
                    is_active=True,
                    created_by=user_id,
                )
                assignment = repo.save(assignment)
                assignments.append(assignment)
        
        # Insert sales orders for each assignment
        with DatabaseConnection() as db:
            for i, assignment in enumerate(assignments):
                db.session.execute(text("""
                    INSERT INTO sales_orders (assignment_id, session_id, payment_method, total)
                    VALUES 
                        (:assignment_id, :session_id, 'cash', :amount1),
                        (:assignment_id, :session_id, 'sinpe', :amount2)
                """), {
                    "assignment_id": str(assignment.assignment_id),
                    "session_id": str(sessions[i].session_id),
                    "amount1": 100.0 * (i + 1),
                    "amount2": 200.0 * (i + 1)
                })
            db.session.commit()
        
        # Get dashboard data
        dashboard = dashboard_service.get_dashboard_data(org_id, user_id)
        
        # Verify dashboard data
        assert dashboard is not None
        assert len(dashboard.stands) == 2
        
        # Verify global KPIs
        assert dashboard.total_revenue == 900.0  # (100+200) + (200+400)
        assert dashboard.total_sales == 4
        assert dashboard.avg_ticket == 225.0
        
        # Cleanup
        with DatabaseConnection() as db:
            for assignment in assignments:
                db.session.execute(text("""
                    DELETE FROM sales_orders WHERE assignment_id = :assignment_id
                """), {"assignment_id": str(assignment.assignment_id)})
            db.session.commit()
        
        with AssignmentRepository() as repo:
            for assignment in assignments:
                repo.delete(str(assignment.assignment_id))
        with SessionRepository() as repo:
            for session in sessions:
                repo.delete(str(session.session_id))
        with BranchRepository() as repo:
            for branch in branches:
                repo.delete(str(branch.branch_id))

    def test_get_dashboard_filter_by_session_id(self, test_setup):
        """Test filtering dashboard by specific session_id."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create another session
        with SessionRepository() as repo:
            other_session = Session(
                session_id=uuid.uuid4(),
                organization_id=org_id,
                branch_id=branch.branch_id,
                name="Other Session",
                type="shift",
                context="caja",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            other_session = repo.save(other_session)
        
        # Create another assignment for the other session
        with AssignmentRepository() as repo:
            other_assignment = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=other_session.session_id,
                user_id=f"other-user-{uuid.uuid4()}",
                branch_id=branch.branch_id,
                terminal_id=None,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            other_assignment = repo.save(other_assignment)
        
        # Insert sales orders for both sessions
        with DatabaseConnection() as db:
            db.session.execute(text("""
                INSERT INTO sales_orders (assignment_id, session_id, payment_method, total)
                VALUES 
                    (:assignment_id1, :session_id1, 'cash', 100.00),
                    (:assignment_id2, :session_id2, 'cash', 200.00)
            """), {
                "assignment_id1": str(assignment.assignment_id),
                "session_id1": str(session.session_id),
                "assignment_id2": str(other_assignment.assignment_id),
                "session_id2": str(other_session.session_id)
            })
            db.session.commit()
        
        # Get dashboard data filtered by first session
        dashboard = dashboard_service.get_dashboard_data(
            org_id, user_id, session_id=str(session.session_id)
        )
        
        # Verify only first session data is returned
        assert dashboard is not None
        assert len(dashboard.stands) == 1
        assert dashboard.total_revenue == 100.0
        assert dashboard.total_sales == 1
        
        # Get dashboard data filtered by second session
        dashboard = dashboard_service.get_dashboard_data(
            org_id, user_id, session_id=str(other_session.session_id)
        )
        
        # Verify only second session data is returned
        assert dashboard is not None
        assert len(dashboard.stands) == 1
        assert dashboard.total_revenue == 200.0
        assert dashboard.total_sales == 1
        
        # Cleanup
        with DatabaseConnection() as db:
            db.session.execute(text("""
                DELETE FROM sales_orders 
                WHERE assignment_id IN (:assignment_id1, :assignment_id2)
            """), {
                "assignment_id1": str(assignment.assignment_id),
                "assignment_id2": str(other_assignment.assignment_id)
            })
            db.session.commit()
        
        with AssignmentRepository() as repo:
            repo.delete(str(other_assignment.assignment_id))
        with SessionRepository() as repo:
            repo.delete(str(other_session.session_id))

    def test_get_dashboard_sales_aggregation(self, test_setup):
        """Test sales aggregation from sales_orders table."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        
        # Insert sales orders with different payment methods
        with DatabaseConnection() as db:
            db.session.execute(text("""
                INSERT INTO sales_orders (assignment_id, session_id, payment_method, total)
                VALUES 
                    (:assignment_id, :session_id, 'cash', 50.00),
                    (:assignment_id, :session_id, 'cash', 75.00),
                    (:assignment_id, :session_id, 'sinpe', 100.00),
                    (:assignment_id, :session_id, 'sinpe', 150.00),
                    (:assignment_id, :session_id, 'card', 200.00),
                    (:assignment_id, :session_id, 'card', 300.00)
            """), {
                "assignment_id": str(assignment.assignment_id),
                "session_id": str(session.session_id)
            })
            db.session.commit()
        
        # Get dashboard data
        dashboard = dashboard_service.get_dashboard_data(org_id, user_id)
        
        # Verify payment method breakdown
        assert dashboard is not None
        assert len(dashboard.stands) == 1
        
        stand = dashboard.stands[0]
        assert stand.cash == 125.0  # 50 + 75
        assert stand.sinpe == 250.0  # 100 + 150
        assert stand.card == 500.0  # 200 + 300
        assert stand.total_revenue == 875.0
        assert stand.sales_count == 6
        
        # Cleanup
        with DatabaseConnection() as db:
            db.session.execute(text("""
                DELETE FROM sales_orders WHERE assignment_id = :assignment_id
            """), {"assignment_id": str(assignment.assignment_id)})
            db.session.commit()

    def test_get_dashboard_product_ranking(self, test_setup):
        """Test product ranking calculation."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        
        # Create products
        product_ids = [uuid.uuid4() for _ in range(3)]
        
        with DatabaseConnection() as db:
            # Insert products
            for i, product_id in enumerate(product_ids):
                db.session.execute(text("""
                    INSERT INTO products (product_id, organization_id, name, image_url, status)
                    VALUES (:product_id, :org_id, :name, :image_url, 'active')
                """), {
                    "product_id": str(product_id),
                    "org_id": org_id,
                    "name": f"Product {i+1}",
                    "image_url": f"emoji-{i+1}"
                })
            
            # Insert sales orders
            order_ids = [uuid.uuid4() for _ in range(3)]
            for order_id in order_ids:
                db.session.execute(text("""
                    INSERT INTO sales_orders (order_id, assignment_id, session_id, payment_method, total)
                    VALUES (:order_id, :assignment_id, :session_id, 'cash', 100.00)
                """), {
                    "order_id": str(order_id),
                    "assignment_id": str(assignment.assignment_id),
                    "session_id": str(session.session_id)
                })
            
            # Insert order items
            db.session.execute(text("""
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES 
                    (:order_id1, :product_id1, 10, 10.00),
                    (:order_id2, :product_id2, 5, 20.00),
                    (:order_id3, :product_id3, 2, 50.00)
            """), {
                "order_id1": str(order_ids[0]),
                "product_id1": str(product_ids[0]),
                "order_id2": str(order_ids[1]),
                "product_id2": str(product_ids[1]),
                "order_id3": str(order_ids[2]),
                "product_id3": str(product_ids[2])
            })
            
            db.session.commit()
        
        # Get dashboard data
        dashboard = dashboard_service.get_dashboard_data(org_id, user_id)
        
        # Verify product ranking
        assert dashboard is not None
        assert len(dashboard.product_ranking) == 3
        
        # Products should be ordered by revenue descending
        assert dashboard.product_ranking[0].name == "Product 1"
        assert dashboard.product_ranking[0].units == 10
        assert dashboard.product_ranking[0].revenue == 100.0
        
        assert dashboard.product_ranking[1].name == "Product 2"
        assert dashboard.product_ranking[1].units == 5
        assert dashboard.product_ranking[1].revenue == 100.0
        
        assert dashboard.product_ranking[2].name == "Product 3"
        assert dashboard.product_ranking[2].units == 2
        assert dashboard.product_ranking[2].revenue == 100.0
        
        # Cleanup
        with DatabaseConnection() as db:
            db.session.execute(text("""
                DELETE FROM order_items WHERE order_id = ANY(:order_ids)
            """), {"order_ids": [str(oid) for oid in order_ids]})
            db.session.execute(text("""
                DELETE FROM sales_orders WHERE order_id = ANY(:order_ids)
            """), {"order_ids": [str(oid) for oid in order_ids]})
            db.session.execute(text("""
                DELETE FROM products WHERE product_id = ANY(:product_ids)
            """), {"product_ids": [str(pid) for pid in product_ids]})
            db.session.commit()

    def test_get_dashboard_global_kpis_calculation(self, test_setup):
        """Test global KPIs calculation (total_revenue, total_sales, avg_ticket)."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        
        # Insert sales orders
        with DatabaseConnection() as db:
            db.session.execute(text("""
                INSERT INTO sales_orders (assignment_id, session_id, payment_method, total)
                VALUES 
                    (:assignment_id, :session_id, 'cash', 100.00),
                    (:assignment_id, :session_id, 'sinpe', 200.00),
                    (:assignment_id, :session_id, 'card', 300.00),
                    (:assignment_id, :session_id, 'cash', 400.00)
            """), {
                "assignment_id": str(assignment.assignment_id),
                "session_id": str(session.session_id)
            })
            db.session.commit()
        
        # Get dashboard data
        dashboard = dashboard_service.get_dashboard_data(org_id, user_id)
        
        # Verify global KPIs
        assert dashboard is not None
        assert dashboard.total_revenue == 1000.0
        assert dashboard.total_sales == 4
        assert dashboard.avg_ticket == 250.0
        
        # Cleanup
        with DatabaseConnection() as db:
            db.session.execute(text("""
                DELETE FROM sales_orders WHERE assignment_id = :assignment_id
            """), {"assignment_id": str(assignment.assignment_id)})
            db.session.commit()

    def test_get_dashboard_organization_scoped_data_isolation(self, setup_sales_orders_table, test_organization):
        """Test that dashboard data is isolated by organization."""
        org_id_1 = test_organization["id"]
        org_id_2 = f"fake-org-{uuid.uuid4()}"  # This won't have any data
        user_id = test_organization["user_id"]
        
        # Create data for organization 1
        with BranchRepository() as repo:
            branch1 = Branch(
                branch_id=uuid.uuid4(),
                organization_id=org_id_1,
                name="Org 1 Branch",
                code=f"O1B-{uuid.uuid4().hex[:4]}",
                type="stand",
                is_active=True,
                created_by=user_id,
            )
            branch1 = repo.save(branch1)
        
        with SessionRepository() as repo:
            session1 = Session(
                session_id=uuid.uuid4(),
                organization_id=org_id_1,
                branch_id=branch1.branch_id,
                name="Org 1 Session",
                type="match",
                context="gradas",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            session1 = repo.save(session1)
        
        with AssignmentRepository() as repo:
            assignment1 = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id_1,
                session_id=session1.session_id,
                user_id=user_id,
                branch_id=branch1.branch_id,
                terminal_id=None,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            assignment1 = repo.save(assignment1)
        
        # Insert sales for org 1
        with DatabaseConnection() as db:
            db.session.execute(text("""
                INSERT INTO sales_orders (assignment_id, session_id, payment_method, total)
                VALUES (:assignment_id, :session_id, 'cash', 500.00)
            """), {
                "assignment_id": str(assignment1.assignment_id),
                "session_id": str(session1.session_id)
            })
            db.session.commit()
        
        # Get dashboard for org 1
        dashboard1 = dashboard_service.get_dashboard_data(org_id_1, user_id)
        assert dashboard1 is not None
        assert len(dashboard1.stands) == 1
        assert dashboard1.total_revenue == 500.0
        
        # Get dashboard for org 2 (should be empty - fake org with no data)
        dashboard2 = dashboard_service.get_dashboard_data(org_id_2, user_id)
        assert dashboard2 is not None
        assert len(dashboard2.stands) == 0
        assert dashboard2.total_revenue == 0.0
        
        # Cleanup
        with DatabaseConnection() as db:
            db.session.execute(text("""
                DELETE FROM sales_orders WHERE assignment_id = :assignment_id
            """), {"assignment_id": str(assignment1.assignment_id)})
            db.session.commit()
        
        with AssignmentRepository() as repo:
            repo.delete(str(assignment1.assignment_id))
        with SessionRepository() as repo:
            repo.delete(str(session1.session_id))
        with BranchRepository() as repo:
            repo.delete(str(branch1.branch_id))


    # ========================================
    # HTTP Endpoint Tests with TestClient
    # ========================================

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        app = FastApiConfig().get_app()
        return TestClient(app)

    def test_http_get_dashboard_endpoint_success(self, client, test_setup):
        """Test GET /api/users/{userId}/organization/{orgId}/dashboard endpoint."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Insert sales orders
        with DatabaseConnection() as db:
            db.session.execute(text("""
                INSERT INTO sales_orders (assignment_id, session_id, payment_method, total)
                VALUES 
                    (:assignment_id, :session_id, 'cash', 100.00),
                    (:assignment_id, :session_id, 'sinpe', 150.00),
                    (:assignment_id, :session_id, 'card', 200.00)
            """), {
                "assignment_id": str(assignment.assignment_id),
                "session_id": str(session.session_id)
            })
            db.session.commit()
        
        # Make HTTP request
        response = client.get(
            f"/api/users/{user_id}/organization/{org_id}/dashboard"
        )
        
        # Verify HTTP status code
        assert response.status_code == 200
        
        # Verify response format
        data = response.json()
        assert "stands" in data
        assert "total_revenue" in data
        assert "total_sales" in data
        assert "avg_ticket" in data
        assert "product_ranking" in data
        
        # Verify data content
        assert len(data["stands"]) == 1
        stand = data["stands"][0]
        assert stand["id"] == str(branch.branch_id)
        assert stand["name"] == "Test Branch"
        assert stand["cashier_name"] == user_id
        assert stand["context"] == "gradas"
        assert stand["total_revenue"] == 450.0
        assert stand["sales_count"] == 3
        assert stand["cash"] == 100.0
        assert stand["sinpe"] == 150.0
        assert stand["card"] == 200.0
        assert stand["last_sync_at"] > 0
        
        assert data["total_revenue"] == 450.0
        assert data["total_sales"] == 3
        assert data["avg_ticket"] == 150.0
        
        # Cleanup
        with DatabaseConnection() as db:
            db.session.execute(text("""
                DELETE FROM sales_orders WHERE assignment_id = :assignment_id
            """), {"assignment_id": str(assignment.assignment_id)})
            db.session.commit()

    def test_http_get_dashboard_with_session_id_filter(self, client, test_setup):
        """Test GET /api/users/{userId}/organization/{orgId}/dashboard?session_id={sessionId}."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        branch = test_setup['branch']
        
        # Create another session
        with SessionRepository() as repo:
            other_session = Session(
                session_id=uuid.uuid4(),
                organization_id=org_id,
                branch_id=branch.branch_id,
                name="Other Session",
                type="shift",
                context="caja",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            other_session = repo.save(other_session)
        
        # Create another assignment for the other session
        with AssignmentRepository() as repo:
            other_assignment = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id,
                session_id=other_session.session_id,
                user_id=f"other-user-{uuid.uuid4()}",
                branch_id=branch.branch_id,
                terminal_id=None,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            other_assignment = repo.save(other_assignment)
        
        # Insert sales orders for both sessions
        with DatabaseConnection() as db:
            db.session.execute(text("""
                INSERT INTO sales_orders (assignment_id, session_id, payment_method, total)
                VALUES 
                    (:assignment_id1, :session_id1, 'cash', 100.00),
                    (:assignment_id2, :session_id2, 'cash', 200.00)
            """), {
                "assignment_id1": str(assignment.assignment_id),
                "session_id1": str(session.session_id),
                "assignment_id2": str(other_assignment.assignment_id),
                "session_id2": str(other_session.session_id)
            })
            db.session.commit()
        
        # Make HTTP request with session_id filter
        response = client.get(
            f"/api/users/{user_id}/organization/{org_id}/dashboard",
            params={"session_id": str(session.session_id)}
        )
        
        # Verify HTTP status code
        assert response.status_code == 200
        
        # Verify only first session data is returned
        data = response.json()
        assert len(data["stands"]) == 1
        assert data["total_revenue"] == 100.0
        assert data["total_sales"] == 1
        
        # Cleanup
        with DatabaseConnection() as db:
            db.session.execute(text("""
                DELETE FROM sales_orders 
                WHERE assignment_id IN (:assignment_id1, :assignment_id2)
            """), {
                "assignment_id1": str(assignment.assignment_id),
                "assignment_id2": str(other_assignment.assignment_id)
            })
            db.session.commit()
        
        with AssignmentRepository() as repo:
            repo.delete(str(other_assignment.assignment_id))
        with SessionRepository() as repo:
            repo.delete(str(other_session.session_id))

    def test_http_get_dashboard_empty_response(self, client, test_organization):
        """Test GET /api/users/{userId}/organization/{orgId}/dashboard with no active sessions."""
        org_id = test_organization["id"]
        user_id = test_organization["user_id"]
        
        # Make HTTP request
        response = client.get(
            f"/api/users/{user_id}/organization/{org_id}/dashboard"
        )
        
        # Verify HTTP status code
        assert response.status_code == 200
        
        # Verify empty dashboard
        data = response.json()
        assert data["stands"] == []
        assert data["total_revenue"] == 0.0
        assert data["total_sales"] == 0
        assert data["avg_ticket"] == 0.0
        assert data["product_ranking"] == []

    def test_http_get_dashboard_multiple_stands(self, client, setup_sales_orders_table, test_organization):
        """Test GET /api/users/{userId}/organization/{orgId}/dashboard with multiple stands."""
        org_id = test_organization["id"]
        user_id = test_organization["user_id"]
        
        # Create branches
        branches = []
        with BranchRepository() as repo:
            for i in range(3):
                branch = Branch(
                    branch_id=uuid.uuid4(),
                    organization_id=org_id,
                    name=f"Stand {i+1}",
                    code=f"S{i+1}-{uuid.uuid4().hex[:4]}",
                    type="stand",
                    is_active=True,
                    created_by=user_id,
                )
                branch = repo.save(branch)
                branches.append(branch)
        
        # Create sessions
        sessions = []
        with SessionRepository() as repo:
            for i, branch in enumerate(branches):
                session = Session(
                    session_id=uuid.uuid4(),
                    organization_id=org_id,
                    branch_id=branch.branch_id,
                    name=f"Session {i+1}",
                    type="match",
                    context="gradas",
                    start_time=datetime.now(timezone.utc),
                    is_active=True,
                    created_by=user_id,
                )
                session = repo.save(session)
                sessions.append(session)
        
        # Create assignments
        assignments = []
        with AssignmentRepository() as repo:
            for i, (session, branch) in enumerate(zip(sessions, branches)):
                assignment = Assignment(
                    assignment_id=uuid.uuid4(),
                    organization_id=org_id,
                    session_id=session.session_id,
                    user_id=f"cashier-{i+1}",
                    branch_id=branch.branch_id,
                    terminal_id=None,
                    role="cashier",
                    start_time=datetime.now(timezone.utc),
                    is_active=True,
                    created_by=user_id,
                )
                assignment = repo.save(assignment)
                assignments.append(assignment)
        
        # Insert sales orders for each assignment
        with DatabaseConnection() as db:
            for i, assignment in enumerate(assignments):
                db.session.execute(text("""
                    INSERT INTO sales_orders (assignment_id, session_id, payment_method, total)
                    VALUES 
                        (:assignment_id, :session_id, 'cash', :amount)
                """), {
                    "assignment_id": str(assignment.assignment_id),
                    "session_id": str(sessions[i].session_id),
                    "amount": 100.0 * (i + 1)
                })
            db.session.commit()
        
        # Make HTTP request
        response = client.get(
            f"/api/users/{user_id}/organization/{org_id}/dashboard"
        )
        
        # Verify HTTP status code
        assert response.status_code == 200
        
        # Verify multiple stands
        data = response.json()
        assert len(data["stands"]) == 3
        assert data["total_revenue"] == 600.0  # 100 + 200 + 300
        assert data["total_sales"] == 3
        assert data["avg_ticket"] == 200.0
        
        # Cleanup
        with DatabaseConnection() as db:
            for assignment in assignments:
                db.session.execute(text("""
                    DELETE FROM sales_orders WHERE assignment_id = :assignment_id
                """), {"assignment_id": str(assignment.assignment_id)})
            db.session.commit()
        
        with AssignmentRepository() as repo:
            for assignment in assignments:
                repo.delete(str(assignment.assignment_id))
        with SessionRepository() as repo:
            for session in sessions:
                repo.delete(str(session.session_id))
        with BranchRepository() as repo:
            for branch in branches:
                repo.delete(str(branch.branch_id))

    def test_http_get_dashboard_with_product_ranking(self, client, test_setup):
        """Test GET /api/users/{userId}/organization/{orgId}/dashboard with product ranking."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        assignment = test_setup['assignment']
        session = test_setup['session']
        
        # Create products
        product_ids = [uuid.uuid4() for _ in range(5)]
        
        with DatabaseConnection() as db:
            # Insert products
            for i, product_id in enumerate(product_ids):
                db.session.execute(text("""
                    INSERT INTO products (product_id, organization_id, name, image_url, status)
                    VALUES (:product_id, :org_id, :name, :image_url, 'active')
                """), {
                    "product_id": str(product_id),
                    "org_id": org_id,
                    "name": f"Product {i+1}",
                    "image_url": f"🍗"
                })
            
            # Insert sales orders
            order_ids = [uuid.uuid4() for _ in range(5)]
            for order_id in order_ids:
                db.session.execute(text("""
                    INSERT INTO sales_orders (order_id, assignment_id, session_id, payment_method, total)
                    VALUES (:order_id, :assignment_id, :session_id, 'cash', 100.00)
                """), {
                    "order_id": str(order_id),
                    "assignment_id": str(assignment.assignment_id),
                    "session_id": str(session.session_id)
                })
            
            # Insert order items with different revenues
            for i, (order_id, product_id) in enumerate(zip(order_ids, product_ids)):
                db.session.execute(text("""
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                    VALUES (:order_id, :product_id, :quantity, :unit_price)
                """), {
                    "order_id": str(order_id),
                    "product_id": str(product_id),
                    "quantity": 5 - i,  # 5, 4, 3, 2, 1
                    "unit_price": 10.0 * (i + 1)  # 10, 20, 30, 40, 50
                })
            
            db.session.commit()
        
        # Make HTTP request
        response = client.get(
            f"/api/users/{user_id}/organization/{org_id}/dashboard"
        )
        
        # Verify HTTP status code
        assert response.status_code == 200
        
        # Verify product ranking
        data = response.json()
        assert len(data["product_ranking"]) == 5
        
        # Products should be ordered by revenue descending
        # Product 5: 1 * 50 = 50
        # Product 4: 2 * 40 = 80
        # Product 3: 3 * 30 = 90
        # Product 2: 4 * 20 = 80
        # Product 1: 5 * 10 = 50
        # Expected order: Product 3 (90), Product 4 (80), Product 2 (80), Product 1 (50), Product 5 (50)
        
        assert data["product_ranking"][0]["name"] == "Product 3"
        assert data["product_ranking"][0]["revenue"] == 90.0
        assert data["product_ranking"][0]["units"] == 3
        
        # Cleanup
        with DatabaseConnection() as db:
            db.session.execute(text("""
                DELETE FROM order_items WHERE order_id = ANY(:order_ids)
            """), {"order_ids": [str(oid) for oid in order_ids]})
            db.session.execute(text("""
                DELETE FROM sales_orders WHERE order_id = ANY(:order_ids)
            """), {"order_ids": [str(oid) for oid in order_ids]})
            db.session.execute(text("""
                DELETE FROM products WHERE product_id = ANY(:product_ids)
            """), {"product_ids": [str(pid) for pid in product_ids]})
            db.session.commit()

    def test_http_get_dashboard_response_field_naming(self, client, test_setup):
        """Test that dashboard response uses snake_case field naming."""
        org_id = test_setup['org_id']
        user_id = test_setup['user_id']
        
        # Make HTTP request
        response = client.get(
            f"/api/users/{user_id}/organization/{org_id}/dashboard"
        )
        
        # Verify HTTP status code
        assert response.status_code == 200
        
        # Verify snake_case field naming
        data = response.json()
        assert "total_revenue" in data
        assert "total_sales" in data
        assert "avg_ticket" in data
        assert "product_ranking" in data
        
        # Verify stand fields use snake_case
        if len(data["stands"]) > 0:
            stand = data["stands"][0]
            assert "cashier_name" in stand
            assert "total_revenue" in stand
            assert "sales_count" in stand
            assert "last_sync_at" in stand

    def test_http_get_dashboard_organization_isolation(self, client, setup_sales_orders_table, test_organization):
        """Test that dashboard data is isolated by organization via HTTP endpoint."""
        org_id_1 = test_organization["id"]
        org_id_2 = f"fake-org-{uuid.uuid4()}"  # This won't have any data
        user_id = test_organization["user_id"]
        
        # Create data for organization 1
        with BranchRepository() as repo:
            branch1 = Branch(
                branch_id=uuid.uuid4(),
                organization_id=org_id_1,
                name="Org 1 Branch",
                code=f"O1B-{uuid.uuid4().hex[:4]}",
                type="stand",
                is_active=True,
                created_by=user_id,
            )
            branch1 = repo.save(branch1)
        
        with SessionRepository() as repo:
            session1 = Session(
                session_id=uuid.uuid4(),
                organization_id=org_id_1,
                branch_id=branch1.branch_id,
                name="Org 1 Session",
                type="match",
                context="gradas",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            session1 = repo.save(session1)
        
        with AssignmentRepository() as repo:
            assignment1 = Assignment(
                assignment_id=uuid.uuid4(),
                organization_id=org_id_1,
                session_id=session1.session_id,
                user_id=user_id,
                branch_id=branch1.branch_id,
                terminal_id=None,
                role="cashier",
                start_time=datetime.now(timezone.utc),
                is_active=True,
                created_by=user_id,
            )
            assignment1 = repo.save(assignment1)
        
        # Insert sales for org 1
        with DatabaseConnection() as db:
            db.session.execute(text("""
                INSERT INTO sales_orders (assignment_id, session_id, payment_method, total)
                VALUES (:assignment_id, :session_id, 'cash', 500.00)
            """), {
                "assignment_id": str(assignment1.assignment_id),
                "session_id": str(session1.session_id)
            })
            db.session.commit()
        
        # Make HTTP request for org 1
        response1 = client.get(
            f"/api/users/{user_id}/organization/{org_id_1}/dashboard"
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["stands"]) == 1
        assert data1["total_revenue"] == 500.0
        
        # Make HTTP request for org 2 (should be empty - fake org with no data)
        response2 = client.get(
            f"/api/users/{user_id}/organization/{org_id_2}/dashboard"
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["stands"]) == 0
        assert data2["total_revenue"] == 0.0
        
        # Cleanup
        with DatabaseConnection() as db:
            db.session.execute(text("""
                DELETE FROM sales_orders WHERE assignment_id = :assignment_id
            """), {"assignment_id": str(assignment1.assignment_id)})
            db.session.commit()
        
        with AssignmentRepository() as repo:
            repo.delete(str(assignment1.assignment_id))
        with SessionRepository() as repo:
            repo.delete(str(session1.session_id))
        with BranchRepository() as repo:
            repo.delete(str(branch1.branch_id))
