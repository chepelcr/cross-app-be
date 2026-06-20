"""Unit tests for the notifications feed controller (stub)."""
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.controllers.notifications_controller import NotificationsController


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Mount only the notifications controller onto a bare FastAPI app.

    This keeps the test fully unit-scoped — no DB, no other controllers, no
    middleware — so it can run inside `tests/unit` without external setup.
    """
    app = FastAPI()
    NotificationsController(app)
    return TestClient(app)


class TestNotificationsFeedEndpoint:
    """GET /api/notifications — stub feed contract."""

    def test_returns_empty_data_and_cursor_iso_timestamp(self, client: TestClient):
        response = client.get("/api/notifications")

        assert response.status_code == 200
        body = response.json()

        assert "data" in body
        assert body["data"] == []

        assert "cursor" in body
        # cursor must be a parseable ISO-8601 timestamp
        cursor = body["cursor"]
        assert isinstance(cursor, str)
        # FastAPI/pydantic serialise datetimes as ISO strings; this should parse.
        parsed = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
        assert isinstance(parsed, datetime)

    def test_accepts_since_query_param_and_still_returns_empty(
        self, client: TestClient
    ):
        response = client.get(
            "/api/notifications",
            params={"since": "2024-01-01T00:00:00Z"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["data"] == []
        assert "cursor" in body
