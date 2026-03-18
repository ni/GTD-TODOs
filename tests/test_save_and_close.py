"""Tests for the Save-and-Close navigation bug.

When a user hits Save (staying on the edit page) and then hits Save and
Close, they should be redirected to the *original* page they came from —
not back to the edit page.

The root cause: after Save redirects to the edit page, the Referer
header points at the edit page itself, so back_url is lost.  The fix
should preserve back_url through successive Save round-trips.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.services.project_service import create_project  # noqa: I001
from app.services.task_service import create_task

# ---------------------------------------------------------------------------
# Task: Save then Save-and-Close preserves original back_url
# ---------------------------------------------------------------------------

class TestTaskSaveAndClose:
    """Save-and-Close on task edit should return to the original page."""

    def test_save_then_close_returns_to_original_page(
        self, client: TestClient, db_session: Session
    ) -> None:
        """After Save + Save-and-Close, user returns to the page they
        originally navigated from, not the edit page."""
        task = create_task(db_session, title="Fix bug")

        # Step 1: Hit Save (action=save) with back_url=/inbox
        resp = client.post(
            f"/tasks/{task.id}/update",
            data={
                "title": "Fix bug",
                "status": "inbox",
                "action": "save",
                "back_url": "/inbox",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303
        save_redirect = resp.headers["location"]
        # The redirect should stay on the edit page
        assert f"/tasks/{task.id}/edit" in save_redirect

        # Step 2: Follow that redirect (GET the edit page)
        resp = client.get(save_redirect)
        assert resp.status_code == 200

        # The hidden back_url in the form should still be /inbox
        assert 'value="/inbox"' in resp.text

        # Step 3: Now hit Save and Close (action=close) with the same back_url
        resp = client.post(
            f"/tasks/{task.id}/update",
            data={
                "title": "Fix bug",
                "status": "inbox",
                "action": "close",
                "back_url": "/inbox",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303
        assert resp.headers["location"] == "/inbox"

    def test_save_preserves_back_url_in_redirect(
        self, client: TestClient, db_session: Session
    ) -> None:
        """When Save redirects to the edit page, back_url should be
        passed as a query parameter so the GET handler can pick it up."""
        task = create_task(db_session, title="Test task")

        resp = client.post(
            f"/tasks/{task.id}/update",
            data={
                "title": "Test task",
                "status": "inbox",
                "action": "save",
                "back_url": "/today",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303
        location = resp.headers["location"]
        # The redirect URL should carry back_url as a query param
        assert "back_url=" in location
        assert "/today" in location

    def test_edit_page_uses_query_param_over_referer(
        self, client: TestClient, db_session: Session
    ) -> None:
        """The edit page should prefer back_url from the query string
        over the Referer header."""
        task = create_task(db_session, title="Query vs Referer")

        # Simulate: query param says /today, but Referer says /tasks/1/edit
        resp = client.get(
            f"/tasks/{task.id}/edit?back_url=/today",
            headers={"referer": f"http://testserver/tasks/{task.id}/edit"},
        )
        assert resp.status_code == 200
        assert 'value="/today"' in resp.text

    def test_multiple_saves_preserve_back_url(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Hitting Save multiple times should not lose the original back_url."""
        task = create_task(db_session, title="Multi-save")

        # First save
        resp = client.post(
            f"/tasks/{task.id}/update",
            data={
                "title": "Multi-save",
                "status": "inbox",
                "action": "save",
                "back_url": "/projects/5",
            },
            follow_redirects=False,
        )
        location1 = resp.headers["location"]
        assert "back_url=" in location1

        # Follow redirect, then save again
        resp = client.get(location1)
        assert 'value="/projects/5"' in resp.text


# ---------------------------------------------------------------------------
# Project: Save then Save-and-Close preserves original back_url
# ---------------------------------------------------------------------------

class TestProjectSaveAndClose:
    """Save-and-Close on project edit should return to the original page."""

    def test_save_then_close_returns_to_original_page(
        self, client: TestClient, db_session: Session
    ) -> None:
        """After Save + Save-and-Close, user returns to the page they
        originally navigated from, not the project detail page."""
        project = create_project(db_session, name="My Project")

        # Step 1: Hit Save with back_url=/projects
        resp = client.post(
            f"/projects/{project.id}/update",
            data={
                "name": "My Project",
                "description": "",
                "notes": "",
                "due_date": "",
                "action": "save",
                "back_url": "/projects",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303
        save_redirect = resp.headers["location"]
        assert f"/projects/{project.id}/edit" in save_redirect

        # Step 2: Follow redirect to GET the edit page
        resp = client.get(save_redirect)
        assert resp.status_code == 200

        # The hidden back_url should be /projects
        assert 'value="/projects"' in resp.text

        # Step 3: Hit Save and Close
        resp = client.post(
            f"/projects/{project.id}/update",
            data={
                "name": "My Project",
                "description": "",
                "notes": "",
                "due_date": "",
                "action": "close",
                "back_url": "/projects",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303
        assert resp.headers["location"] == "/projects"

    def test_save_preserves_back_url_in_redirect(
        self, client: TestClient, db_session: Session
    ) -> None:
        """When Save redirects to the edit page, back_url should be
        passed as a query parameter."""
        project = create_project(db_session, name="Redirect Test")

        resp = client.post(
            f"/projects/{project.id}/update",
            data={
                "name": "Redirect Test",
                "description": "",
                "notes": "",
                "due_date": "",
                "action": "save",
                "back_url": "/projects",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303
        location = resp.headers["location"]
        assert "back_url=" in location
        assert "/projects" in location

    def test_project_edit_page_has_back_url(
        self, client: TestClient, db_session: Session
    ) -> None:
        """The project edit page should have a hidden back_url field."""
        project = create_project(db_session, name="BackURL Test")

        resp = client.get(
            f"/projects/{project.id}/edit",
            headers={"referer": "http://testserver/projects"},
        )
        assert resp.status_code == 200
        assert 'name="back_url"' in resp.text
        assert 'value="/projects"' in resp.text

    def test_project_close_uses_back_url_not_hardcoded(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Save-and-Close should use back_url, not always redirect to
        the project detail page."""
        project = create_project(db_session, name="Close Test")

        resp = client.post(
            f"/projects/{project.id}/update",
            data={
                "name": "Close Test",
                "description": "",
                "notes": "",
                "due_date": "",
                "action": "close",
                "back_url": "/projects",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303
        # Should go to /projects (from back_url), NOT /projects/{id}
        assert resp.headers["location"] == "/projects"

    def test_edit_page_uses_query_param_over_referer(
        self, client: TestClient, db_session: Session
    ) -> None:
        """The project edit page should prefer back_url from the query
        string over the Referer header."""
        project = create_project(db_session, name="QP Test")

        resp = client.get(
            f"/projects/{project.id}/edit?back_url=/today",
            headers={"referer": f"http://testserver/projects/{project.id}/edit"},
        )
        assert resp.status_code == 200
        assert 'value="/today"' in resp.text
