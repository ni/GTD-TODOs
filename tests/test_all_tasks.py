"""Tests for Phase 4: All Tasks page, filtering, search, and UX polish."""

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import RecurrenceType, TaskStatus
from app.services.project_service import create_project
from app.services.task_service import create_task

# ---------------------------------------------------------------------------
# All Tasks page – basic
# ---------------------------------------------------------------------------


class TestAllTasksPage:
    def test_returns_html(self, client: TestClient) -> None:
        response = client.get("/tasks")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    def test_shows_all_tasks(self, client: TestClient, db_session: Session) -> None:
        create_task(db_session, title="Alpha")
        create_task(db_session, title="Beta", status=TaskStatus.DONE)
        create_task(db_session, title="Gamma", status=TaskStatus.NEXT_ACTION)
        response = client.get("/tasks")
        assert "Alpha" in response.text
        assert "Beta" in response.text
        assert "Gamma" in response.text

    def test_empty_state(self, client: TestClient) -> None:
        response = client.get("/tasks")
        assert response.status_code == 200
        # Should show an empty-state message
        assert "No tasks" in response.text or "empty" in response.text.lower()

    def test_nav_link_present(self, client: TestClient) -> None:
        response = client.get("/tasks")
        assert 'href="/tasks"' in response.text


# ---------------------------------------------------------------------------
# Filter by status
# ---------------------------------------------------------------------------


class TestAllTasksFilterStatus:
    def test_filter_by_inbox(self, client: TestClient, db_session: Session) -> None:
        create_task(db_session, title="Inbox filter item")
        create_task(db_session, title="Done filter item", status=TaskStatus.DONE)
        response = client.get("/tasks?status=inbox")
        assert "Inbox filter item" in response.text
        assert "Done filter item" not in response.text

    def test_filter_by_done(self, client: TestClient, db_session: Session) -> None:
        create_task(db_session, title="Inbox filter item")
        create_task(db_session, title="Done filter item", status=TaskStatus.DONE)
        response = client.get("/tasks?status=done")
        assert "Inbox filter item" not in response.text
        assert "Done filter item" in response.text

    def test_filter_by_next_action(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(db_session, title="Next action item", status=TaskStatus.NEXT_ACTION)
        create_task(db_session, title="Inbox only item", status=TaskStatus.INBOX)
        response = client.get("/tasks?status=next_action")
        assert "Next action item" in response.text
        assert "Inbox only item" not in response.text

    def test_invalid_status_shows_all(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(db_session, title="Task A")
        response = client.get("/tasks?status=bogus")
        assert "Task A" in response.text


# ---------------------------------------------------------------------------
# Filter by project
# ---------------------------------------------------------------------------


class TestAllTasksFilterProject:
    def test_filter_by_project(self, client: TestClient, db_session: Session) -> None:
        proj = create_project(db_session, name="Work")
        create_task(db_session, title="Work task", project_id=proj.id)
        create_task(db_session, title="Personal task")
        response = client.get(f"/tasks?project_id={proj.id}")
        assert "Work task" in response.text
        assert "Personal task" not in response.text

    def test_filter_by_no_project(
        self, client: TestClient, db_session: Session
    ) -> None:
        proj = create_project(db_session, name="Work")
        create_task(db_session, title="Work task", project_id=proj.id)
        create_task(db_session, title="Orphan task")
        response = client.get("/tasks?project_id=none")
        assert "Orphan task" in response.text
        assert "Work task" not in response.text


# ---------------------------------------------------------------------------
# Filter by due-date presence
# ---------------------------------------------------------------------------


class TestAllTasksFilterDueDate:
    def test_filter_has_due_date(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(
            db_session, title="With date", due_date=date.today()
        )
        create_task(db_session, title="No date")
        response = client.get("/tasks?has_due_date=yes")
        assert "With date" in response.text
        assert "No date" not in response.text

    def test_filter_no_due_date(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(
            db_session, title="With date", due_date=date.today()
        )
        create_task(db_session, title="No date")
        response = client.get("/tasks?has_due_date=no")
        assert "No date" in response.text
        assert "With date" not in response.text


# ---------------------------------------------------------------------------
# Filter by recurring
# ---------------------------------------------------------------------------


class TestAllTasksFilterRecurring:
    def test_filter_recurring(self, client: TestClient, db_session: Session) -> None:
        create_task(
            db_session,
            title="Recurring task",
            is_recurring=True,
            recurrence_type=RecurrenceType.DAILY,
            due_date=date.today(),
        )
        create_task(db_session, title="One-shot task")
        response = client.get("/tasks?is_recurring=yes")
        assert "Recurring task" in response.text
        assert "One-shot task" not in response.text

    def test_filter_non_recurring(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(
            db_session,
            title="Recurring task",
            is_recurring=True,
            recurrence_type=RecurrenceType.DAILY,
            due_date=date.today(),
        )
        create_task(db_session, title="One-shot task")
        response = client.get("/tasks?is_recurring=no")
        assert "One-shot task" in response.text
        assert "Recurring task" not in response.text


# ---------------------------------------------------------------------------
# Search by title and notes
# ---------------------------------------------------------------------------


class TestAllTasksSearch:
    def test_search_by_title(self, client: TestClient, db_session: Session) -> None:
        create_task(db_session, title="Buy groceries")
        create_task(db_session, title="Write report")
        response = client.get("/tasks?q=groceries")
        assert "Buy groceries" in response.text
        assert "Write report" not in response.text

    def test_search_by_notes(self, client: TestClient, db_session: Session) -> None:
        create_task(db_session, title="Task A", notes="Remember to call dentist")
        create_task(db_session, title="Task B", notes="Pick up laundry")
        response = client.get("/tasks?q=dentist")
        assert "Task A" in response.text
        assert "Task B" not in response.text

    def test_search_case_insensitive(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(db_session, title="Buy Groceries")
        response = client.get("/tasks?q=buy")
        assert "Buy Groceries" in response.text

    def test_search_empty_query_shows_all(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(db_session, title="Task X")
        create_task(db_session, title="Task Y")
        response = client.get("/tasks?q=")
        assert "Task X" in response.text
        assert "Task Y" in response.text


# ---------------------------------------------------------------------------
# Combined filters
# ---------------------------------------------------------------------------


class TestAllTasksCombinedFilters:
    def test_filter_status_and_project(
        self, client: TestClient, db_session: Session
    ) -> None:
        proj = create_project(db_session, name="Work")
        create_task(
            db_session,
            title="Work inbox",
            project_id=proj.id,
            status=TaskStatus.INBOX,
        )
        create_task(
            db_session,
            title="Work done",
            project_id=proj.id,
            status=TaskStatus.DONE,
        )
        create_task(db_session, title="Personal inbox", status=TaskStatus.INBOX)
        response = client.get(f"/tasks?status=inbox&project_id={proj.id}")
        assert "Work inbox" in response.text
        assert "Work done" not in response.text
        assert "Personal inbox" not in response.text

    def test_search_with_status_filter(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(db_session, title="Buy milk", status=TaskStatus.INBOX)
        create_task(db_session, title="Buy eggs", status=TaskStatus.DONE)
        response = client.get("/tasks?q=buy&status=inbox")
        assert "Buy milk" in response.text
        assert "Buy eggs" not in response.text


# ---------------------------------------------------------------------------
# Markdown notes rendered safely on All Tasks
# ---------------------------------------------------------------------------


class TestAllTasksMarkdown:
    def test_markdown_rendered(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(db_session, title="MD Task", notes="**bold text**")
        response = client.get("/tasks")
        assert "<strong>bold text</strong>" in response.text

    def test_unsafe_html_sanitized(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(
            db_session,
            title="XSS Task",
            notes="<script>alert('xss')</script>",
        )
        response = client.get("/tasks")
        assert "<script>" not in response.text


# ---------------------------------------------------------------------------
# Visual distinction classes
# ---------------------------------------------------------------------------


class TestAllTasksVisualDistinction:
    def test_overdue_task_has_class(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(
            db_session,
            title="Overdue item",
            due_date=date.today() - timedelta(days=2),
            status=TaskStatus.NEXT_ACTION,
        )
        response = client.get("/tasks")
        assert "task-overdue" in response.text

    def test_due_today_task_has_class(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(
            db_session,
            title="Today item",
            due_date=date.today(),
            status=TaskStatus.NEXT_ACTION,
        )
        response = client.get("/tasks")
        assert "task-due-today" in response.text

    def test_done_task_has_class(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(db_session, title="Finished item", status=TaskStatus.DONE)
        response = client.get("/tasks")
        assert "task-done" in response.text

    def test_inbox_task_has_class(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(db_session, title="Inbox item", status=TaskStatus.INBOX)
        response = client.get("/tasks")
        assert "task-inbox" in response.text


# ---------------------------------------------------------------------------
# Validation: update route rejects bad input
# ---------------------------------------------------------------------------


class TestValidationMessages:
    def test_update_task_empty_title_rejected(
        self, client: TestClient, db_session: Session
    ) -> None:
        task = create_task(db_session, title="Valid")
        response = client.post(
            f"/tasks/{task.id}/update",
            data={"title": "", "status": "inbox"},
            follow_redirects=False,
        )
        # Should either redirect back with an error or return 422
        assert response.status_code in (303, 422)
        # Original title should be preserved
        db_session.expire_all()
        from app.services.task_service import get_task

        t = get_task(db_session, task.id)  # type: ignore[arg-type]
        assert t is not None
        assert t.title == "Valid"


# ---------------------------------------------------------------------------
# Redirect: update and complete redirect back to /tasks when referred from it
# ---------------------------------------------------------------------------


class TestAllTasksRedirects:
    def test_complete_from_tasks_page_redirects_back(
        self, client: TestClient, db_session: Session
    ) -> None:
        task = create_task(db_session, title="Complete me")
        response = client.post(
            f"/tasks/{task.id}/complete",
            headers={"referer": "http://testserver/tasks"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/tasks" in response.headers["location"]

    def test_update_redirects_back_to_referer(
        self, client: TestClient, db_session: Session
    ) -> None:
        task = create_task(db_session, title="Update me")
        response = client.post(
            f"/tasks/{task.id}/update",
            data={"title": "Updated", "status": "inbox"},
            headers={"referer": "http://testserver/tasks?status=inbox"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/tasks" in response.headers["location"]
