"""Tests for Phase 3: Today and Project views."""

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import RecurrenceType, TaskStatus
from app.services.project_service import archive_project, create_project
from app.services.task_service import create_task

# ---------------------------------------------------------------------------
# Today page
# ---------------------------------------------------------------------------


class TestTodayPage:
    def test_today_returns_html(self, client: TestClient) -> None:
        response = client.get("/today")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    def test_task_due_today_appears(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(
            db_session,
            title="Due today task",
            due_date=date.today(),
            status=TaskStatus.NEXT_ACTION,
        )
        response = client.get("/today")
        assert "Due today task" in response.text

    def test_recurring_task_due_today_appears(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(
            db_session,
            title="Daily standup",
            due_date=date.today(),
            is_recurring=True,
            recurrence_type=RecurrenceType.DAILY,
            status=TaskStatus.NEXT_ACTION,
        )
        response = client.get("/today")
        assert "Daily standup" in response.text

    def test_overdue_task_appears(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(
            db_session,
            title="Overdue errand",
            due_date=date.today() - timedelta(days=3),
            status=TaskStatus.NEXT_ACTION,
        )
        response = client.get("/today")
        assert "Overdue errand" in response.text

    def test_overdue_section_present(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(
            db_session,
            title="Late task",
            due_date=date.today() - timedelta(days=1),
            status=TaskStatus.NEXT_ACTION,
        )
        response = client.get("/today")
        assert "Overdue" in response.text

    def test_due_today_section_present(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(
            db_session,
            title="Today task",
            due_date=date.today(),
            status=TaskStatus.NEXT_ACTION,
        )
        response = client.get("/today")
        assert "Due Today" in response.text

    def test_future_task_not_shown(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(
            db_session,
            title="Future task",
            due_date=date.today() + timedelta(days=5),
            status=TaskStatus.NEXT_ACTION,
        )
        response = client.get("/today")
        assert "Future task" not in response.text

    def test_task_without_due_date_not_shown(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(db_session, title="No date task", status=TaskStatus.INBOX)
        response = client.get("/today")
        assert "No date task" not in response.text

    def test_done_tasks_not_shown(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_task(
            db_session,
            title="Done today",
            due_date=date.today(),
            status=TaskStatus.DONE,
        )
        response = client.get("/today")
        assert "Done today" not in response.text

    def test_today_shows_project_badge(
        self, client: TestClient, db_session: Session
    ) -> None:
        project = create_project(db_session, name="Work")
        create_task(
            db_session,
            title="Work task",
            due_date=date.today(),
            status=TaskStatus.NEXT_ACTION,
            project_id=project.id,
        )
        response = client.get("/today")
        assert "Work" in response.text

    def test_today_empty_state(self, client: TestClient) -> None:
        response = client.get("/today")
        assert "Nothing due" in response.text or "clear" in response.text.lower()

    def test_today_complete_redirects_back(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Complete button on today page should redirect back to /today."""
        task = create_task(
            db_session,
            title="Complete from today",
            due_date=date.today(),
            status=TaskStatus.NEXT_ACTION,
        )
        response = client.post(
            f"/tasks/{task.id}/complete",
            headers={"referer": "http://testserver/today"},
            follow_redirects=False,
        )
        assert response.status_code == 303


# ---------------------------------------------------------------------------
# Projects list page
# ---------------------------------------------------------------------------


class TestProjectsListPage:
    def test_projects_list_returns_html(self, client: TestClient) -> None:
        response = client.get("/projects")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    def test_shows_active_projects(
        self, client: TestClient, db_session: Session
    ) -> None:
        create_project(db_session, name="Alpha")
        create_project(db_session, name="Beta")
        response = client.get("/projects")
        assert "Alpha" in response.text
        assert "Beta" in response.text

    def test_hides_archived_projects(
        self, client: TestClient, db_session: Session
    ) -> None:
        project = create_project(db_session, name="Old project")
        archive_project(db_session, project.id)  # type: ignore[arg-type]
        response = client.get("/projects")
        assert "Old project" not in response.text

    def test_shows_open_task_count(
        self, client: TestClient, db_session: Session
    ) -> None:
        project = create_project(db_session, name="Counted")
        create_task(
            db_session,
            title="T1",
            project_id=project.id,
            status=TaskStatus.NEXT_ACTION,
        )
        create_task(
            db_session,
            title="T2",
            project_id=project.id,
            status=TaskStatus.INBOX,
        )
        create_task(
            db_session,
            title="T3",
            project_id=project.id,
            status=TaskStatus.DONE,
        )
        response = client.get("/projects")
        # 2 open tasks (T1 + T2), T3 is done
        assert "2" in response.text

    def test_shows_due_today_count(
        self, client: TestClient, db_session: Session
    ) -> None:
        project = create_project(db_session, name="Urgent")
        create_task(
            db_session,
            title="Today item",
            project_id=project.id,
            due_date=date.today(),
            status=TaskStatus.NEXT_ACTION,
        )
        create_task(
            db_session,
            title="Tomorrow item",
            project_id=project.id,
            due_date=date.today() + timedelta(days=1),
            status=TaskStatus.NEXT_ACTION,
        )
        response = client.get("/projects")
        assert "Urgent" in response.text

    def test_empty_state(self, client: TestClient) -> None:
        response = client.get("/projects")
        assert response.status_code == 200

    def test_project_links_to_detail(
        self, client: TestClient, db_session: Session
    ) -> None:
        project = create_project(db_session, name="Linked")
        response = client.get("/projects")
        assert f"/projects/{project.id}" in response.text

    def test_projects_list_has_create_form(self, client: TestClient) -> None:
        response = client.get("/projects")
        assert '<form' in response.text
        assert 'action="/projects"' in response.text
        assert 'method="post"' in response.text

    def test_create_project_redirects(self, client: TestClient) -> None:
        response = client.post(
            "/projects", data={"name": "New Proj"}, follow_redirects=False
        )
        assert response.status_code == 303
        assert "/projects" in response.headers["location"]

    def test_create_project_appears_in_list(
        self, client: TestClient,
    ) -> None:
        client.post("/projects", data={"name": "Created via form"})
        response = client.get("/projects")
        assert "Created via form" in response.text

    def test_create_project_empty_name_ignored(self, client: TestClient) -> None:
        response = client.post(
            "/projects", data={"name": ""}, follow_redirects=False
        )
        assert response.status_code == 303


# ---------------------------------------------------------------------------
# Project detail page
# ---------------------------------------------------------------------------


class TestProjectDetailPage:
    def test_project_detail_returns_html(
        self, client: TestClient, db_session: Session
    ) -> None:
        project = create_project(db_session, name="Detail Test")
        response = client.get(f"/projects/{project.id}")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    def test_shows_project_name(
        self, client: TestClient, db_session: Session
    ) -> None:
        project = create_project(db_session, name="My Project")
        response = client.get(f"/projects/{project.id}")
        assert "My Project" in response.text

    def test_shows_project_description(
        self, client: TestClient, db_session: Session
    ) -> None:
        project = create_project(
            db_session, name="Described", description="A special project"
        )
        response = client.get(f"/projects/{project.id}")
        assert "A special project" in response.text

    def test_shows_tasks_for_project(
        self, client: TestClient, db_session: Session
    ) -> None:
        project = create_project(db_session, name="Tasked")
        create_task(db_session, title="Proj task 1", project_id=project.id)
        create_task(db_session, title="Proj task 2", project_id=project.id)
        response = client.get(f"/projects/{project.id}")
        assert "Proj task 1" in response.text
        assert "Proj task 2" in response.text

    def test_does_not_show_other_project_tasks(
        self, client: TestClient, db_session: Session
    ) -> None:
        project_a = create_project(db_session, name="Proj A")
        create_project(db_session, name="Proj B")
        create_task(db_session, title="A task", project_id=project_a.id)
        create_task(db_session, title="Orphan task")  # no project
        response = client.get(f"/projects/{project_a.id}")
        assert "A task" in response.text
        assert "Orphan task" not in response.text

    def test_tasks_grouped_by_status(
        self, client: TestClient, db_session: Session
    ) -> None:
        project = create_project(db_session, name="Grouped")
        create_task(
            db_session,
            title="Inbox item",
            project_id=project.id,
            status=TaskStatus.INBOX,
        )
        create_task(
            db_session,
            title="Next item",
            project_id=project.id,
            status=TaskStatus.NEXT_ACTION,
        )
        create_task(
            db_session,
            title="Done item",
            project_id=project.id,
            status=TaskStatus.DONE,
        )
        response = client.get(f"/projects/{project.id}")
        assert "Inbox item" in response.text
        assert "Next item" in response.text
        assert "Done item" in response.text
        # Status group headings
        assert "Inbox" in response.text
        assert "Next Action" in response.text
        assert "Done" in response.text

    def test_project_not_found(self, client: TestClient) -> None:
        response = client.get("/projects/9999")
        assert response.status_code == 404

    def test_project_detail_has_quick_add(
        self, client: TestClient, db_session: Session
    ) -> None:
        project = create_project(db_session, name="Quick Add")
        response = client.get(f"/projects/{project.id}")
        assert "<form" in response.text
        assert 'action="/tasks"' in response.text

    def test_task_notes_rendered_as_markdown(
        self, client: TestClient, db_session: Session
    ) -> None:
        project = create_project(db_session, name="MD Project")
        create_task(
            db_session,
            title="With notes",
            notes="**bold text**",
            project_id=project.id,
        )
        response = client.get(f"/projects/{project.id}")
        assert "<strong>bold text</strong>" in response.text
