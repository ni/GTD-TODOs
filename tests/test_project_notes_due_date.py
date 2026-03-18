"""Tests for project notes, due dates, and overdue counting."""

from datetime import date, timedelta

from sqlmodel import Session

from app.services.project_service import (
    count_overdue_projects,
    create_project,
    update_project,
)
from app.services.task_service import get_nav_counts

# --- Model / Service layer ---


def test_create_project_with_notes_and_due_date(db_session: Session) -> None:
    project = create_project(
        db_session,
        name="Launch",
        notes="## Plan\n- step one\n- step two",
        due_date=date(2026, 6, 1),
    )

    assert project.notes == "## Plan\n- step one\n- step two"
    assert project.due_date == date(2026, 6, 1)


def test_create_project_defaults_notes_and_due_date_to_none(
    db_session: Session,
) -> None:
    project = create_project(db_session, name="Plain")

    assert project.notes is None
    assert project.due_date is None


def test_update_project_notes_and_due_date(db_session: Session) -> None:
    project = create_project(db_session, name="Evolving")

    updated = update_project(
        db_session,
        project.id,  # type: ignore[arg-type]
        notes="New note",
        due_date=date(2026, 12, 31),
    )

    assert updated is not None
    assert updated.notes == "New note"
    assert updated.due_date == date(2026, 12, 31)


def test_update_project_clear_notes_and_due_date(db_session: Session) -> None:
    project = create_project(
        db_session, name="Clearable", notes="old", due_date=date(2026, 1, 1)
    )

    updated = update_project(
        db_session,
        project.id,  # type: ignore[arg-type]
        notes=None,
        due_date=None,
    )

    assert updated is not None
    assert updated.notes is None
    assert updated.due_date is None


def test_update_project_leaves_fields_unchanged_when_unset(
    db_session: Session,
) -> None:
    project = create_project(
        db_session, name="Stable", notes="keep me", due_date=date(2026, 3, 1)
    )

    updated = update_project(db_session, project.id, name="Stable Renamed")  # type: ignore[arg-type]

    assert updated is not None
    assert updated.notes == "keep me"
    assert updated.due_date == date(2026, 3, 1)


# --- Overdue project counting ---


def test_count_overdue_projects_none(db_session: Session) -> None:
    create_project(db_session, name="NoDue")
    create_project(
        db_session, name="Future", due_date=date.today() + timedelta(days=30)
    )

    assert count_overdue_projects(db_session) == 0


def test_count_overdue_projects_excludes_completed_and_archived(
    db_session: Session,
) -> None:
    from app.services.project_service import archive_project, complete_project
    from app.services.task_service import complete_task, create_task

    yesterday = date.today() - timedelta(days=1)

    # Overdue and active → should count
    create_project(db_session, name="Active Overdue", due_date=yesterday)

    # Overdue but archived → should NOT count
    p_archived = create_project(
        db_session, name="Archived Overdue", due_date=yesterday
    )
    archive_project(db_session, p_archived.id)  # type: ignore[arg-type]

    # Overdue but completed → should NOT count
    p_completed = create_project(
        db_session, name="Completed Overdue", due_date=yesterday
    )
    # Need all tasks done to complete
    t = create_task(db_session, title="Done", project_id=p_completed.id)
    complete_task(db_session, t.id)  # type: ignore[arg-type]
    complete_project(db_session, p_completed.id)  # type: ignore[arg-type]

    assert count_overdue_projects(db_session) == 1


def test_count_overdue_projects_today_not_overdue(db_session: Session) -> None:
    create_project(db_session, name="DueToday", due_date=date.today())

    assert count_overdue_projects(db_session) == 0


# --- Nav counts include overdue_projects ---


def test_nav_counts_includes_overdue_projects(db_session: Session) -> None:
    yesterday = date.today() - timedelta(days=1)
    create_project(db_session, name="Overdue Proj", due_date=yesterday)

    counts = get_nav_counts(db_session)

    assert "overdue_projects" in counts
    assert counts["overdue_projects"] == 1


# --- Migration idempotency ---


def test_migration_adds_columns_idempotently(sqlite_database_url: str) -> None:
    from app.db import init_db

    # Call init twice — should not raise
    init_db(sqlite_database_url)
    init_db(sqlite_database_url)


# --- Route tests ---


def test_project_edit_page(client) -> None:
    # Create a project first
    client.post("/projects", data={"name": "EditMe"})
    # Find the project
    resp = client.get("/projects")
    assert resp.status_code == 200

    # Get project detail to confirm id=1
    resp = client.get("/projects/1/edit")
    assert resp.status_code == 200
    assert "EditMe" in resp.text
    assert "Notes" in resp.text
    assert "Due Date" in resp.text
    assert "Save and Close" in resp.text


def test_project_edit_page_not_found(client) -> None:
    resp = client.get("/projects/9999/edit")
    assert resp.status_code == 404


def test_project_update_saves_notes_and_due_date(client) -> None:
    client.post("/projects", data={"name": "Updatable"})

    resp = client.post(
        "/projects/1/update",
        data={
            "name": "Updatable",
            "description": "",
            "notes": "# Hello\nworld",
            "due_date": "2026-07-01",
            "action": "close",
        },
    )
    assert resp.status_code == 200  # follows redirect

    # Check the detail page shows notes and due date
    resp = client.get("/projects/1")
    assert resp.status_code == 200
    assert "Hello" in resp.text
    assert "2026-07-01" in resp.text


def test_project_update_save_stays_on_edit(client) -> None:
    client.post("/projects", data={"name": "SaveStay"})

    resp = client.post(
        "/projects/1/update",
        data={
            "name": "SaveStay",
            "description": "",
            "notes": "",
            "due_date": "",
            "action": "save",
        },
    )
    # Should redirect to edit page (303 -> 200 after follow)
    assert resp.status_code == 200
    assert "Edit Project" in resp.text


def test_project_detail_shows_due_date_and_notes(client) -> None:
    client.post("/projects", data={"name": "Detailed"})
    client.post(
        "/projects/1/update",
        data={
            "name": "Detailed",
            "description": "",
            "notes": "Some **bold** text",
            "due_date": "2026-05-15",
            "action": "close",
        },
    )

    resp = client.get("/projects/1")
    assert resp.status_code == 200
    assert "2026-05-15" in resp.text
    assert "<strong>bold</strong>" in resp.text


def test_project_detail_edit_link(client) -> None:
    client.post("/projects", data={"name": "WithEdit"})

    resp = client.get("/projects/1")
    assert resp.status_code == 200
    assert "/projects/1/edit" in resp.text


def test_projects_list_shows_due_date(client) -> None:
    client.post("/projects", data={"name": "Listed"})
    client.post(
        "/projects/1/update",
        data={
            "name": "Listed",
            "description": "",
            "notes": "",
            "due_date": "2026-09-01",
            "action": "close",
        },
    )

    resp = client.get("/projects")
    assert resp.status_code == 200
    assert "2026-09-01" in resp.text


def test_nav_shows_overdue_projects_badge(client) -> None:
    from datetime import timedelta

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    client.post("/projects", data={"name": "OverdueNav"})
    client.post(
        "/projects/1/update",
        data={
            "name": "OverdueNav",
            "description": "",
            "notes": "",
            "due_date": yesterday,
            "action": "close",
        },
    )

    resp = client.get("/inbox")
    assert resp.status_code == 200
    assert "nav-badge-red" in resp.text
    # The badge should be near the Projects link
    assert "Projects" in resp.text


def test_task_edit_has_project_due_date_data_attrs(client) -> None:
    client.post("/projects", data={"name": "ProjDue"})
    client.post(
        "/projects/1/update",
        data={
            "name": "ProjDue",
            "description": "",
            "notes": "",
            "due_date": "2026-04-01",
            "action": "close",
        },
    )
    # Create a task in that project
    client.post("/tasks", data={"title": "MyTask", "project_id": "1"})

    resp = client.get("/tasks/1/edit", headers={"referer": "http://testserver/inbox"})
    assert resp.status_code == 200
    assert 'data-due-date="2026-04-01"' in resp.text
