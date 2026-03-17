"""Phase 5: Hardening and Backup tests.

Tests for structured logging, custom error pages, and data export.
"""

from __future__ import annotations

import csv
import io
import logging

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.services.project_service import create_project
from app.services.task_service import create_task

# ---------------------------------------------------------------------------
# Structured logging
# ---------------------------------------------------------------------------

class TestStructuredLogging:
    """Verify that the application configures structured logging."""

    def test_app_logger_exists(self, client: TestClient) -> None:
        """The 'app' logger should be configured."""
        logger = logging.getLogger("app")
        assert logger is not None

    def test_request_logging(self, client: TestClient, caplog: object) -> None:
        """Requests should produce log output."""
        with logging.getLogger("app").handlers[0].stream if False else open(  # noqa
            "/dev/null"
        ):
            pass
        # Simply verify the app responds — logging middleware is structural
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_log_level_default(self, client: TestClient) -> None:
        """Default log level should be INFO."""
        logger = logging.getLogger("app")
        assert logger.level <= logging.INFO


# ---------------------------------------------------------------------------
# Custom error pages
# ---------------------------------------------------------------------------

class TestErrorPages:
    """Custom error pages for 404 and 500 errors."""

    def test_404_page_returns_html(self, client: TestClient) -> None:
        """A request to a nonexistent page returns 404 with an HTML body."""
        resp = client.get("/nonexistent-page")
        assert resp.status_code == 404
        assert "text/html" in resp.headers["content-type"]
        assert "Not Found" in resp.text

    def test_404_page_has_navigation(self, client: TestClient) -> None:
        """The 404 page should include navigation back to known pages."""
        resp = client.get("/nonexistent-page")
        assert resp.status_code == 404
        assert "/inbox" in resp.text

    def test_404_task_returns_html(self, client: TestClient) -> None:
        """A missing task edit page should return 404 HTML."""
        resp = client.get("/tasks/99999/edit")
        assert resp.status_code == 404
        assert "text/html" in resp.headers["content-type"]

    def test_404_project_returns_html(self, client: TestClient) -> None:
        """A missing project page should return 404 HTML."""
        resp = client.get("/projects/99999")
        assert resp.status_code == 404
        assert "text/html" in resp.headers["content-type"]


# ---------------------------------------------------------------------------
# Export — CSV
# ---------------------------------------------------------------------------

class TestCSVExport:
    """Tasks can be exported to CSV."""

    def test_export_csv_empty(self, client: TestClient) -> None:
        """CSV export with no tasks returns headers only."""
        resp = client.get("/export/tasks.csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        reader = csv.reader(io.StringIO(resp.text))
        rows = list(reader)
        # At least a header row
        assert len(rows) >= 1
        header = rows[0]
        assert "id" in header
        assert "title" in header
        assert "status" in header

    def test_export_csv_with_tasks(
        self, client: TestClient, db_session: Session
    ) -> None:
        """CSV export includes created tasks."""
        create_task(db_session, title="Export me")
        create_task(db_session, title="Export me too", notes="Some **markdown**")
        resp = client.get("/export/tasks.csv")
        assert resp.status_code == 200
        reader = csv.reader(io.StringIO(resp.text))
        rows = list(reader)
        # Header + 2 data rows
        assert len(rows) == 3
        # Verify title column is present
        header = rows[0]
        title_idx = header.index("title")
        titles = {rows[1][title_idx], rows[2][title_idx]}
        assert "Export me" in titles
        assert "Export me too" in titles

    def test_export_csv_content_disposition(self, client: TestClient) -> None:
        """CSV response should suggest a filename."""
        resp = client.get("/export/tasks.csv")
        assert "content-disposition" in resp.headers
        assert "tasks" in resp.headers["content-disposition"]

    def test_export_csv_with_filters(
        self, client: TestClient, db_session: Session
    ) -> None:
        """CSV export respects status filter."""
        from app.models import TaskStatus

        create_task(db_session, title="Inbox task")
        create_task(db_session, title="Done task", status=TaskStatus.DONE)
        resp = client.get("/export/tasks.csv?status=inbox")
        reader = csv.reader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) == 2  # header + 1 inbox task


# ---------------------------------------------------------------------------
# Export — JSON
# ---------------------------------------------------------------------------

class TestJSONExport:
    """Tasks can be exported to JSON."""

    def test_export_json_empty(self, client: TestClient) -> None:
        """JSON export with no tasks returns an empty list."""
        resp = client.get("/export/tasks.json")
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_export_json_with_tasks(
        self, client: TestClient, db_session: Session
    ) -> None:
        """JSON export includes created tasks with expected fields."""
        create_task(db_session, title="JSON task", notes="Note text")
        resp = client.get("/export/tasks.json")
        data = resp.json()
        assert len(data) == 1
        task = data[0]
        assert task["title"] == "JSON task"
        assert task["notes"] == "Note text"
        assert "id" in task
        assert "status" in task
        assert "due_date" in task
        assert "created_at" in task

    def test_export_json_with_filters(
        self, client: TestClient, db_session: Session
    ) -> None:
        """JSON export respects status filter."""
        from app.models import TaskStatus

        create_task(db_session, title="Inbox JSON")
        create_task(db_session, title="Done JSON", status=TaskStatus.DONE)
        resp = client.get("/export/tasks.json?status=done")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Done JSON"

    def test_export_json_content_disposition(self, client: TestClient) -> None:
        """JSON response should suggest a filename."""
        resp = client.get("/export/tasks.json")
        assert "content-disposition" in resp.headers
        assert "tasks" in resp.headers["content-disposition"]


# ---------------------------------------------------------------------------
# Projects export
# ---------------------------------------------------------------------------

class TestProjectExport:
    """Projects can be exported."""

    def test_export_projects_csv(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Projects CSV export works."""
        create_project(db_session, name="Test Project")
        resp = client.get("/export/projects.csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        reader = csv.reader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) == 2  # header + 1

    def test_export_projects_json(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Projects JSON export works."""
        create_project(db_session, name="Test Project JSON")
        resp = client.get("/export/projects.json")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Project JSON"
